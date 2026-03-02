# HEAR-UI Backend

> FastAPI backend for Cochlear Implant outcome prediction with ML model and SHAP explanations.

For project-level documentation, see the main [README](../README.md).

---

## Overview

The backend provides a REST API for:
- **ML Predictions** — probability of successful CI outcome (0–100%)
- **Explainable AI** — SHAP feature importance, coefficient-based, and LIME explanations
- **Patient Management** — CRUD operations for patient records
- **Feedback Collection** — store and retrieve clinical feedback

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.114+ |
| ORM | SQLModel (SQLAlchemy 2.0 async) |
| Database | PostgreSQL 15 |
| Migrations | Alembic |
| ML Model | scikit-learn (RandomForest) |
| Explainability | SHAP (TreeExplainer), coefficient-based, LIME |
| Testing | pytest (coverage ≥69%, enforced in CI) |
| Linting | Ruff (linter + formatter) |
| Type Checking | mypy |

---

## Setup

### With Docker (recommended)

```bash
# From project root
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build

# Verify
curl http://localhost:8000/api/v1/utils/health-check/

# View logs
docker compose -f docker/docker-compose.yml logs -f backend
```

### Local Development (without Docker)

```bash
cd backend
pip install -r requirements.txt   # or: uv sync

# Set environment variables
export DATABASE_URL=postgresql://postgres:password@localhost:5432/hear_db

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/utils/health-check/` | GET | Health status |
| `/api/v1/predict/` | POST | Single ML prediction |
| `/api/v1/predict/batch` | POST | Batch predictions |
| `/api/v1/explainer/explain` | POST | SHAP/coefficient/LIME explanation |
| `/api/v1/patients/` | GET/POST | List & create patients |
| `/api/v1/patients/{id}` | GET/PUT/DELETE | Patient CRUD |
| `/api/v1/patients/{id}/predict` | POST | Predict for stored patient |
| `/api/v1/patients/{id}/explain` | POST | Explain for stored patient |
| `/api/v1/feedback/` | GET/POST | Feedback management |
| `/api/v1/features/` | GET | Available model features |
| `/api/v1/config/` | GET | Frontend configuration |
| `/api/v1/model-card/` | GET | Model documentation |
| `/docs` | GET | Swagger UI |

Interactive docs: http://localhost:8000/docs

### Example Requests

```bash
# Prediction
curl -X POST http://localhost:8000/api/v1/predict/ \
  -H "Content-Type: application/json" \
  -d '{"Alter [J]": 45, "Geschlecht": "w", "Primäre Sprache": "Deutsch"}'

# SHAP explanation
curl -X POST http://localhost:8000/api/v1/explainer/explain \
  -H "Content-Type: application/json" \
  -d '{"age": 45, "gender": "w", "implant_type": "Cochlear"}'
```

---

## Testing

```bash
# In Docker (recommended)
docker compose -f docker/docker-compose.yml exec backend \
  python -m pytest app/tests/ -v --cov=app --cov-report=term-missing

# Local
cd backend && pytest app/tests/ -v --cov=app
```

Current results are reported by the CI pipeline. Coverage threshold: ≥69%.

### Test Categories

| Category | Description |
|----------|-------------|
| Unit Tests | Core logic (model wrapper, preprocessor, explainers) |
| API Route Tests | All REST endpoints |
| Integration Tests | Database operations, model loading |
| SHAP Tests | Explainer correctness and consistency |
| Consistency Tests | Predict vs. explainer alignment |

---

## Database Migrations

```bash
# Apply migrations
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head

# Create new migration
docker compose -f docker/docker-compose.yml exec backend \
  alembic revision --autogenerate -m "Description"

# Rollback one step
docker compose -f docker/docker-compose.yml exec backend alembic downgrade -1
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entrypoint, app.state.model_wrapper
│   ├── api/
│   │   ├── api.py           # Route registration
│   │   ├── deps.py          # Dependency injection
│   │   └── routes/          # API endpoint handlers
│   ├── core/
│   │   ├── model_wrapper.py       # ML model loading & inference
│   │   ├── preprocessor.py        # Feature preprocessing pipeline
│   │   ├── shap_explainer.py      # SHAP TreeExplainer
│   │   ├── rf_dataset_adapter.py  # RandomForest dataset adapter
│   │   ├── alternative_explainers.py  # Coefficient & LIME explainers
│   │   └── explainer_registry.py  # Explainer factory
│   ├── db/                  # Database connection, CRUD, models
│   ├── models/              # SQLModel schemas + trained .pkl model
│   ├── config/              # Feature definitions, locales, model cards
│   └── tests/               # Test suite
├── alembic.ini              # Alembic configuration
├── Dockerfile               # Container build
├── pyproject.toml           # Python project config (Ruff, pytest, mypy)
└── requirements.txt         # Python dependencies
```

---

## CI/CD

GitHub Actions pipeline ([backend-ci.yml](../.github/workflows/backend-ci.yml)):

1. **Lint & Format** — Ruff check and format verification
2. **Type Check** — mypy static analysis
3. **Unit & Integration Tests** — pytest with PostgreSQL service, coverage ≥69%
4. **DB Migration Check** — Alembic apply/rollback validation
5. **E2E API Tests** — Playwright against Docker Compose stack
6. **Docker Build + Security Scan** — Trivy vulnerability scanning
7. **Smoke Tests** — Container runtime health checks

---

## Linting & Formatting

```bash
# Check
ruff check app/

# Auto-fix
ruff check app/ --fix

# Format
ruff format app/

# Type checking
mypy app/ --config-file=pyproject.toml
```

---

## License

MIT License — see [LICENSE](../LICENSE)

