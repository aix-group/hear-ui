import uuid
from datetime import UTC

from sqlmodel import Session, func, select

from app.models import (
    Feedback,
    FeedbackCreate,
    Patient,
    PatientCreate,
    Prediction,
    PredictionCreate,
)


# ------------------------------------------------------------
# Feedback CRUD
# ------------------------------------------------------------
def create_feedback(session: Session, feedback_in: FeedbackCreate) -> Feedback:
    db_obj = Feedback(**feedback_in.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_feedback(session: Session, feedback_id: uuid.UUID | str) -> Feedback | None:
    # Convert string to UUID if needed
    if isinstance(feedback_id, str):
        feedback_id = uuid.UUID(feedback_id)
    statement = select(Feedback).where(Feedback.id == feedback_id)
    result = session.exec(statement)
    return result.first()


def list_feedback(
    session: Session, limit: int = 100, offset: int = 0
) -> list[Feedback]:
    statement = select(Feedback).offset(offset).limit(limit)
    return session.exec(statement).all()  # type: ignore[return-value]


def count_feedback(session: Session) -> int:
    statement = select(func.count()).select_from(Feedback)
    return session.exec(statement).one()


# ------------------------------------------------------------
# Prediction CRUD
# ------------------------------------------------------------
def create_prediction(session: Session, prediction_in: PredictionCreate) -> Prediction:
    db_obj = Prediction(**prediction_in.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_prediction(
    session: Session, prediction_id: uuid.UUID | str
) -> Prediction | None:
    # Convert string to UUID if needed
    if isinstance(prediction_id, str):
        prediction_id = uuid.UUID(prediction_id)
    statement = select(Prediction).where(Prediction.id == prediction_id)
    result = session.exec(statement)
    return result.first()


def list_predictions(
    session: Session, limit: int = 100, offset: int = 0
) -> list[Prediction]:
    statement = select(Prediction).offset(offset).limit(limit)
    return session.exec(statement).all()  # type: ignore[return-value]


# ------------------------------------------------------------
# Patient CRUD
# ------------------------------------------------------------
def find_duplicate_patient(
    session: Session, display_name: str | None, birth_date: str | None
) -> Patient | None:
    """Return an existing patient with same display_name AND Geburtsdatum, or None."""
    if not display_name or not birth_date:
        return None
    statement = select(Patient).where(
        Patient.display_name == display_name,
    )
    candidates = session.exec(statement).all()
    for patient in candidates:
        features = patient.input_features or {}
        if str(features.get("Geburtsdatum", "")).strip() == birth_date.strip():
            return patient
    return None


def create_patient(session: Session, patient_in: PatientCreate) -> Patient:
    db_obj = Patient(**patient_in.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_patient(session: Session, patient_id: uuid.UUID | str) -> Patient | None:
    # Convert string to UUID if needed
    if isinstance(patient_id, str):
        patient_id = uuid.UUID(patient_id)
    statement = select(Patient).where(Patient.id == patient_id)
    result = session.exec(statement)
    return result.first()


def list_patients(session: Session, limit: int = 100, offset: int = 0) -> list[Patient]:
    statement = select(Patient).offset(offset).limit(limit)
    return session.exec(statement).all()  # type: ignore[return-value]


def search_patients_by_name(
    session: Session, q: str, limit: int = 100, offset: int = 0
) -> list[Patient]:
    """Search patients by `display_name` using case-insensitive last-name-start match.

    Only matches patients whose last name (the part before ", ") starts with the
    query.  Format assumed: "Lastname, Firstname" — standard in this application.
    This intentionally does NOT match on first names or substrings in the middle.

    Requires the `display_name` column to be present on the `patient` table.
    """
    # Prefix search on display_name – since the format is "Nachname, Vorname",
    # this matches patients whose last name starts with the query (alphabetical
    # directory-style filtering). Case-insensitive via ilike.
    stmt = select(Patient).where(Patient.display_name.ilike(f"{q}%"))  # type: ignore[union-attr]
    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()  # type: ignore[return-value]


def count_patients(session: Session) -> int:
    """Count total number of patients in database."""
    statement = select(func.count()).select_from(Patient)
    return session.exec(statement).one()


def update_patient(
    session: Session, patient_id: uuid.UUID | str, patient_update: dict
) -> Patient | None:
    """Update a patient's fields (input_features, display_name, etc.).

    Args:
        session: Database session
        patient_id: UUID of the patient to update
        patient_update: Dictionary with fields to update (e.g., {"input_features": {...}, "display_name": "..."})

    Returns:
        Updated Patient object or None if not found
    """
    from datetime import datetime

    if isinstance(patient_id, str):
        patient_id = uuid.UUID(patient_id)

    patient = get_patient(session=session, patient_id=patient_id)
    if not patient:
        return None

    # Update only provided fields
    for key, value in patient_update.items():
        if hasattr(patient, key):
            setattr(patient, key, value)

    # Always update the updated_at timestamp
    patient.updated_at = datetime.now(UTC)

    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


def delete_patient(session: Session, patient_id: uuid.UUID | str) -> bool:
    """Delete a patient from the database (hard delete).

    Args:
        session: Database session
        patient_id: UUID of the patient to delete

    Returns:
        True if patient was deleted, False if not found
    """
    if isinstance(patient_id, str):
        patient_id = uuid.UUID(patient_id)

    patient = get_patient(session=session, patient_id=patient_id)
    if not patient:
        return False

    session.delete(patient)
    session.commit()
    return True
