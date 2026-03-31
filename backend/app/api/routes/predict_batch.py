from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlmodel import Session

from app import crud
from app.api.deps import get_db
from app.models.prediction import PredictionCreate

router = APIRouter(prefix="/patients", tags=["patients"])

# Maximum file size for CSV uploads (10 MB)
MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024

# Maximum number of rows allowed in a single batch upload
MAX_BATCH_ROWS = 5000

# Validation constraints for numeric fields
NUMERIC_CONSTRAINTS: dict[str, tuple[float, float]] = {
    "age": (0, 120),
    "alter": (0, 120),
    "Alter [J]": (0, 120),
    "measure  pre-op": (0, 100),
    "abstand": (0, 36500),  # days — max ~100 years
}

# Basic CSV -> internal column mapping. Extend as needed.
COLUMN_MAPPING = {
    "alter": "age",
    "age": "age",
    "geschlecht": "gender",
    "seiten": "implant_side",
    "primäre sprache": "primary_language",
    "weitere sprachen": "secondary_language",
    "deutsch sprachbarriere": "german_barrier",
    "non-verbal": "non_verbal",
    "eltern m. schwerhörigkeit": "parents_hearing_loss",
    "geschwister m. sh": "siblings_hearing_loss",
    "tinnitus": "tinnitus",
    "schwindel": "dizziness",
    "otorrhoe": "otorrhea",
    "kopfschmerzen": "headache",
    "geschmack": "taste",
    "bildgebung, präoperativ.typ": "imaging_type",
    "bildgebung, präoperativ.befunde": "imaging_findings",
    "objektive messungen.oae (teoae/dpoae)": "oae",
    "objektive messungen.ll": "obj_ll",
    "objektive messungen.4000 hz": "obj_4000hz",
    "hörminderung operiertes ohr": "hearing_loss_op",
    "versorgung operiertes ohr": "care_op_ear",
    "zeitpunkt des hörverlusts (op_ohr)": "time_of_loss",
    "erwerbsart": "acquisition_type",
    "beginn der hörminderung (op-ohr)": "onset_interval",
    "hochgradige hörminderung oder taubheit (op-ohr)": "duration_interval",
    "ursache": "cause",
    "art der hörstörung": "disorder_type",
    "hörminderung gegenohr": "hearing_loss_other_ear",
    "versorgung gegenohr": "care_other_ear",
    "behandlung/op.ci implantation": "implant_details",
    "measure  pre-op": "measure_preop",
    "abstand": "days_between",
}

# Mapping from normalized tokens to the German pipeline column names the model expects.
# These are used for batch uploads so the DataFrame columns match the trained pipeline.
PIPELINE_GERMAN_NAMES = {
    "alter": "Alter [J]",
    "age": "Alter [J]",
    "geschlecht": "Geschlecht",
    "primäre sprache": "Primäre Sprache",
    "primaere sprache": "Primäre Sprache",
    "tinnitus": "Symptome präoperativ.Tinnitus...",
    "beginn der hörminderung": "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...",
    "ursache": "Diagnose.Höranamnese.Ursache....Ursache...",
    "behandlung/op.ci implantation": "Behandlung/OP.CI Implantation",
}


def _to_bool(val: object) -> bool | None:
    """Best-effort boolean parser for German/English values."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("", "nan", "none"):
        return None
    true_vals = {"ja", "yes", "vorhanden", "true", "1", "y"}
    false_vals = {"nein", "no", "kein", "none", "false", "0", "n"}
    if s in true_vals:
        return True
    if s in false_vals:
        return False
    return None


def _parse_interval_to_years(val: object) -> float | None:
    """Map interval labels like '< 1 y', '1-2 y', '2-5 y' to approximate years."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("nan", "", "nicht erhoben", "unbekannt", "unbekannt/ka"):
        return None
    mapping = {
        "< 1 y": 0.5,
        "1-2 y": 1.5,
        "2-5 y": 3.5,
        "5-10 y": 7.5,
        "10-20 y": 15.0,
        "> 20 y": 25.0,
    }
    if s in mapping:
        return mapping[s]
    # try to parse a number
    try:
        return float(s)
    except Exception:
        return None


def _normalize_header(h: str) -> str:
    # remove BOM and invisible unicode BOM char if present, then normalize
    if h is None:
        return ""
    s = str(h)
    # common BOM character \ufeff
    s = s.lstrip("\ufeff")
    return s.strip().lower()


@router.post("/upload", summary="Upload CSV and run batch predictions")
async def upload_csv_and_predict(
    request: Request,
    session: Session = Depends(get_db),
    file: UploadFile = File(...),
    persist: bool = Query(False, description="Persist predictions to DB"),
):
    """Read uploaded CSV, map columns, run predictions row-by-row and optionally persist them.

    This is intentionally simple for the MVP. It reads into pandas, renames headers
    according to `COLUMN_MAPPING` (case-insensitive) and then for each row calls
    `compute_prediction_and_explanation` (existing function).
    """
    import asyncio

    # Use the canonical model wrapper from app state
    model_wrapper = request.app.state.model_wrapper

    if not model_wrapper or not model_wrapper.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate file type
    if file.content_type and file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Expected CSV.",
        )

    # Read CSV into DataFrame
    try:
        contents = await file.read()
        if len(contents) > MAX_CSV_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"CSV file too large ({len(contents)} bytes). Maximum is {MAX_CSV_SIZE_BYTES} bytes.",
            )
        df = pd.read_csv(BytesIO(contents))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {exc}")

    # Drop completely empty rows
    df = df.dropna(how="all")

    if df.empty:
        return {"count": 0, "results": []}

    if len(df) > MAX_BATCH_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"CSV contains {len(df)} rows. Maximum is {MAX_BATCH_ROWS}.",
        )

    # Validate numeric field ranges
    validation_errors: list[str] = []
    for col in df.columns:
        col_stripped = str(col).strip()
        col_lower = col_stripped.lower()
        constraint_key = None
        for key in NUMERIC_CONSTRAINTS:
            if key.lower() == col_lower or key == col_stripped:
                constraint_key = key
                break
        if constraint_key:
            lo, hi = NUMERIC_CONSTRAINTS[constraint_key]
            numeric_vals = pd.to_numeric(df[col], errors="coerce").dropna()
            out_of_range = numeric_vals[(numeric_vals < lo) | (numeric_vals > hi)]
            if not out_of_range.empty:
                validation_errors.append(
                    f"Column '{col}': {len(out_of_range)} values outside allowed range [{lo}, {hi}]"
                )

    if validation_errors:
        raise HTTPException(
            status_code=422,
            detail=f"Validation errors: {'; '.join(validation_errors)}",
        )

    # Run row-by-row predictions in a thread pool to avoid blocking the event loop
    def _process_rows():
        results = []
        for idx, row in df.iterrows():
            row_dict = row.to_dict()

            non_null_values = {
                k: v for k, v in row_dict.items() if pd.notna(v) and str(v).strip() != ""
            }
            if not non_null_values:
                continue

            patient = {}
            for col, val in row_dict.items():
                if pd.isna(val):
                    continue
                patient[col] = val

            try:
                pred_res = model_wrapper.predict(patient)
                try:
                    prediction_value = float(pred_res[0])
                except (TypeError, IndexError):
                    prediction_value = float(pred_res)
                res = {"prediction": prediction_value, "explanation": {}}
            except Exception as e:
                res = {"prediction": None, "error": str(e)}

            results.append(
                {
                    "row": int(idx),
                    "prediction": res.get("prediction"),
                    "explanation": res.get("explanation", {}),
                    "error": res.get("error"),
                    "_patient": patient if persist and res.get("prediction") is not None else None,
                    "_res": res if persist and res.get("prediction") is not None else None,
                }
            )
        return results

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _process_rows)

    # Persist predictions (DB calls) back on the main thread
    for r in results:
        if r.get("_patient") and r.get("_res"):
            try:
                pred_in = PredictionCreate(
                    input_features=r["_patient"],
                    prediction=float(r["_res"].get("prediction", 0.0)),
                    explanation=r["_res"].get("explanation", {}),
                )
                crud.create_prediction(session=session, prediction_in=pred_in)
            except Exception:
                pass

    # Clean up internal keys before returning
    clean_results = [
        {
            "row": r["row"],
            "prediction": r["prediction"],
            "explanation": r["explanation"],
            "error": r.get("error"),
        }
        for r in results
        if r.get("prediction") is not None or r.get("error")
    ]

    return {"count": len(clean_results), "results": clean_results}
