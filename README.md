# HEAR-UI

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.114+-009688.svg)](https://fastapi.tiangolo.com/)
[![Backend Tests](https://img.shields.io/badge/Backend_Tests-542%20passed-brightgreen.svg)](#testing)
[![Backend Coverage](https://img.shields.io/badge/Backend_Coverage-86%25-green.svg)](#testing)
[![Frontend Tests](https://img.shields.io/badge/Frontend_Tests-87%20passed-brightgreen.svg)](#testing)
[![Frontend Coverage](https://img.shields.io/badge/Frontend_Coverage-95%25-brightgreen.svg)](#testing)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-assisted clinical decision support for estimating Cochlear Implant outcomes and explaining predictions via SHAP.

---

**Quick links**: [Getting Started](#getting-started) | [Usage](#usage) | [Development](#development) | [Testing](#testing) | [Architecture](#architecture) | [Contributing](#contributing) | [License](#license)

## About

For hearing-impaired patients, the question arises whether a Cochlear Implant (CI) would help. HEAR-UI supports this decision by providing:

- **ML-based outcome predictions** — estimates the probability of CI success based on patient data
- **Explainable AI (XAI) visualizations** — SHAP feature importance, coefficient-based and LIME explanations
- **User feedback collection** — clinicians can agree/disagree with predictions
- **Patient management** — create, search, and manage patient records

The application is designed as a clinical decision **support** tool — the final decision always rests with the medical professional.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue.js 3, TypeScript, Vite, Vuetify, Plotly.js |
| Backend | FastAPI, SQLModel, scikit-learn, SHAP |
| Database | PostgreSQL |
| Testing | Pytest, Vitest, Playwright |
| Linting | Ruff (backend), Biome (frontend) |
| CI/CD | GitHub Actions |
| Infrastructure | Docker, Docker Compose |

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Git](https://git-scm.com/)

### Quick Start

```bash
git clone <repo-url>
cd hear-ui
cp .env.example .env        # Edit .env with secure values!

docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build
```

**Access the application:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

**Verify:**

```bash
curl http://localhost:8000/api/v1/utils/health-check/
```

### Environment Variables

Copy `.env.example` to `.env` and update values:

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Database password (change from default!) |
| `SECRET_KEY` | JWT signing key (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `DOCKER_IMAGE_BACKEND` | Backend image name (default: `hear-backend`) |
| `DOCKER_IMAGE_FRONTEND` | Frontend image name (default: `hear-frontend`) |

> **Security**: Never commit `.env` with real secrets.

## Usage

### Prediction

```bash
curl -sS -X POST http://localhost:8000/api/v1/predict/ \
  -H "Content-Type: application/json" \
  -d '{"Alter [J]": 45, "Geschlecht": "w", "Primäre Sprache": "Deutsch"}'
```

### SHAP Explanation

```bash
curl -sS -X POST http://localhost:8000/api/v1/explainer/explain \
  -H "Content-Type: application/json" \
  -d '{"age":45, "gender":"w", "implant_type":"Cochlear"}'
```

Full API documentation is available at `/docs` when the backend is running.

## Development

### Backend (without Docker)

```bash
cd backend
pip install -r requirements.txt   # or: uv sync
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### Linting

```bash
# Backend
cd backend && ruff check app/ && ruff format app/

# Frontend
cd frontend && pnpm lint
```

## Testing

### Backend Tests

```bash
# In Docker (recommended)
docker compose -f docker/docker-compose.yml exec backend python -m pytest -v --cov=app

# Local
cd backend && pytest app/tests/ -v --cov=app --cov-report=term-missing
```

**Results**: 542 tests passed | 86% coverage

### Frontend Tests

```bash
cd frontend
pnpm test              # Unit tests (Vitest)
pnpm test:coverage     # With coverage report
pnpm test:e2e          # E2E API tests (Playwright)
pnpm test:e2e:ui       # E2E UI tests (Playwright)
```

**Results**: 87 tests passed | 95% statement coverage

## CI/CD

Automated pipelines run on every push and PR via GitHub Actions:

**Backend CI** ([backend-ci.yml](.github/workflows/backend-ci.yml)):
1. Lint & Format (Ruff)
2. Type Check (mypy)
3. Unit & Integration Tests (with PostgreSQL)
4. DB Migration Check (Alembic)
5. E2E API Tests (Playwright)
6. Docker Build + Security Scan (Trivy)
7. Smoke Tests (container runtime)
8. Coverage Report (minimum 69%)

**Frontend CI** ([frontend-ci.yml](.github/workflows/frontend-ci.yml)):
1. Lint & Format (Biome)
2. Unit Tests (Vitest + coverage)
3. Build Check (TypeScript + Vite)
4. E2E Tests (Playwright)

## Architecture

```
hear-ui/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/routes/     # REST API endpoints
│   │   ├── core/           # ML model wrapper, preprocessor, SHAP explainer
│   │   ├── db/             # Database connection & CRUD
│   │   ├── models/         # SQLModel database models + trained ML model
│   │   └── tests/          # Backend test suite (542 tests)
│   └── requirements.txt
├── frontend/               # Vue.js 3 SPA
│   ├── src/
│   │   ├── components/     # Vue components (feedback, model card, charts)
│   │   ├── routes/         # Page views (patients, predictions, search)
│   │   ├── client/         # Auto-generated API client (OpenAPI)
│   │   └── test/           # Unit tests (87 tests)
│   └── tests/              # Playwright E2E tests
├── docker/                 # Docker Compose orchestration
│   ├── docker-compose.yml
│   └── docker-compose.override.yml
├── .github/workflows/      # CI/CD pipelines
└── patientsData/           # Sample patient CSV data
```

### Core Data Flow

1. Frontend sends patient data to Backend API
2. `ModelWrapper` preprocesses data via `RandomForestDatasetAdapter`
3. `ModelAdapter` runs inference on the loaded ML model
4. Explainer computes SHAP / coefficient / LIME explanations
5. Results returned to frontend; optionally persisted in PostgreSQL

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Maintainers

- Adelia Manafov
- Artem Mozharov
- Niels Kuhl
