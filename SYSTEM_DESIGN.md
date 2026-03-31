# HEAR-UI System Design (Short)

## Overview
HEAR-UI is a Dockerized, web-based system that serves cochlear-implant outcome predictions and explainability. It runs as a multi-service stack with a FastAPI backend, a Vue/Nginx frontend, and a PostgreSQL database. The backend loads a model file from the container filesystem and can generate SHAP (or other) explanations.

## Runtime Topology
- Frontend container: Nginx serves the built Vue app (Vite build).
- Backend container: FastAPI app providing REST API and ML inference.
- Database container: PostgreSQL stores patients and predictions.
- Prestart container: runs DB checks and Alembic migrations before backend starts.
- Optional pgAdmin container in local dev for DB admin.

## Core Data Flow (Predict + Explain)
1. Frontend sends patient data to `POST /api/v1/predict/` or `POST /api/v1/explainer/explain`.
2. Backend validates input, then `ModelWrapper` preprocesses data via `RandomForestDatasetAdapter` and `preprocessor.py`.
3. `ModelAdapter` runs inference on the loaded model file.
4. Optional: explainer runs SHAP (or coefficient/LIME) using background data and feature metadata.
5. Results are returned to the frontend; optional persistence saves a record in Postgres.

## What Is Configurable
- Model file path: `MODEL_PATH` env var (default `backend/app/models/random_forest_final.pkl`).
- SHAP background data: `SHAP_BACKGROUND_FILE` env var or synthetic fallback.
- Explainer method: query param `method=shap|coefficient|lime` on `/explainer/explain`.
- CORS + frontend URL: `FRONTEND_HOST`, `BACKEND_CORS_ORIGINS`.
- Database connection: `POSTGRES_*` vars.
- Frontend API target: build arg `VITE_API_URL`.
- Feature labels/locales: `backend/app/config/feature_definitions.json` and `feature_locales/*.json`.
- Deployment hostnames: `DOMAIN`, `STACK_NAME`, Traefik routing.

## Static vs Interchangeable
Static (assumed stable in current code):
- API contract structure in `backend/app/api/routes/*`.
- 39-feature preprocessing in `backend/app/core/rf_dataset_adapter.py`.
- DB schema and Alembic migrations in `backend/app/alembic`.

Interchangeable (designed to swap with minimal code changes):
- ML model file and framework: `ModelWrapper` auto-detects and uses `ModelAdapter`.
- Dataset adapter: can be replaced to support a new feature schema or dataset format.
- Explainers: SHAP, coefficient, LIME via `ExplainerFactory`.
- Feature labels and localization data in JSON config files.

## Important Constraints
- If you replace the model, its expected input features must match the output of the dataset adapter and preprocessing. If the model requires different features, update the dataset adapter and `preprocessor.py` or introduce a `GenericDatasetAdapter` backed by config.
- The system can run without a model file, but prediction/explainer endpoints return `503` when the model is not loaded.

## Where It Operates
- Local dev: Docker Compose with exposed ports in `docker/docker-compose.override.yml`.
- Production: Docker Compose with Traefik routing and HTTPS.

If you want this as a separate diagram file (e.g. `docs/system.mmd` or `docs/system.svg`), tell me the preferred format and I will generate it.
