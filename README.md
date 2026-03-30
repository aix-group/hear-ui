<p align="center">
  <img height="150px" src="frontend/public/assets/images/Logo.png" alt="HEAR-UI Logo">
</p>

---

**HEAR-UI** is an AI-assisted clinical decision support system designed to estimate Cochlear Implant outcomes and explain predictions using explainable AI (XAI). It provides machine learning-based outcome predictions, interactive SHAP explanations, patient management, and clinical feedback collection — all engineered as a **decision support tool** where the final decision always rests with the medical professional.

**More information:** [Demo video](https://www.youtube.com/watch?v=y3joL_4FiKk) | [System Design](SYSTEM_DESIGN.md) | [Final Report](Report.pdf)

## Quickstart

### Clone repository

```bash
git clone <repo-url>
cd hear-ui
```

### Configure environment

Create a `.env` file based on the template and set the required variables.

```bash
cp .env.example .env
# Edit .env with secure values
```

**Environment Variables:**

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Database password (change from default!) |
| `SECRET_KEY` | Application secret key (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `DOCKER_IMAGE_BACKEND` | Backend image name (default: `hear-backend`) |
| `DOCKER_IMAGE_FRONTEND` | Frontend image name (default: `hear-frontend`) |

> **Security**: Never commit `.env` with real secrets.

### Start containers

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build
```

**Access the application:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation (Swagger) | http://localhost:8000/docs |

**Verify the setup:**

```bash
curl http://localhost:8000/api/v1/utils/health-check/
```

## Features

**Core Capabilities:**

- **ML-based outcome predictions** — estimates the probability of Cochlear Implant success based on patient data
- **Explainable AI (XAI) visualizations** — SHAP waterfall charts with pluggable coefficient-based and LIME explainers
- **User feedback collection** — clinicians can agree/disagree with predictions to improve the system
- **Patient management** — create, search, update, and manage patient records
- **RESTful API** — full API documentation at `/docs`

**Example Requests:**

*Prediction:*
```bash
curl -sS -X POST http://localhost:8000/api/v1/predict/ \
  -H "Content-Type: application/json" \
  -d '{"Alter [J]": 45, "Geschlecht": "w", "Primäre Sprache": "Deutsch"}'
```

*SHAP Explanation:*
```bash
curl -sS -X POST http://localhost:8000/api/v1/explainer/explain \
  -H "Content-Type: application/json" \
  -d '{"age":45, "gender":"w", "implant_type":"Cochlear"}'
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Vue.js 3, TypeScript, Vite, Vuetify, Plotly.js |
| **Backend** | FastAPI, SQLModel, scikit-learn, SHAP |
| **Database** | PostgreSQL |
| **Testing** | Pytest, Vitest, Playwright |
| **Linting & Formatting** | Ruff (backend), Biome (frontend) |
| **CI/CD** | GitHub Actions |
| **Infrastructure** | Docker, Docker Compose |

## Development Instructions

Refer to the following documents for detailed setup and development workflows:

- [Backend](./backend/README.md) — API development, testing, migrations
- [Frontend](./frontend/README.md) — Vue.js components, styling, state management
- [System Design](SYSTEM_DESIGN.md) — architecture, data flow, ML pipeline


## Testing & Quality Assurance

**Backend Tests:**

```bash
# In Docker (recommended)
docker compose -f docker/docker-compose.yml exec backend python -m pytest -v --cov=app

# Local
cd backend && pytest app/tests/ -v --cov=app --cov-report=term-missing
```

**Results (unit tests only):**
- **600 passed, 1 skipped**
- **Test coverage: 75 %** 

**Frontend Tests:**

```bash
cd frontend
pnpm test              # Unit tests (Vitest)
pnpm test:coverage     # Coverage report
pnpm test:e2e          # E2E API tests (Playwright)
pnpm test:e2e:ui       # E2E UI tests (Playwright, requires running backend)
```

**Results:**
- **97 passed** across 12 test files
- **Statement coverage: 96 %**
- **Branch coverage: 74 %**

## CI/CD Pipeline

Automated testing and validation run on every push and pull request via GitHub Actions:

**Backend CI** ([.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml)):
1. Lint & Format (Ruff)
2. Type Check (mypy)
3. Unit & Integration Tests (with PostgreSQL)
4. Database Migration Check (Alembic)
5. E2E API Tests (Playwright)
6. Docker Build
7. Smoke Tests (container runtime)
8. Coverage Report 

**Frontend CI** ([.github/workflows/frontend-ci.yml](.github/workflows/frontend-ci.yml)):
1. Lint & Format (Biome)
2. Unit Tests (Vitest + coverage)
3. Build Check (TypeScript + Vite)
4. E2E Tests (Playwright)

## Architecture and Data Flow

**Project Structure:**

```
hear-ui/
├── backend/                    # FastAPI REST API
│   ├── app/
│   │   ├── api/routes/         # REST API endpoints
│   │   ├── core/               # ML model, preprocessor, SHAP explainer
│   │   ├── db/                 # Database connection & CRUD operations
│   │   ├── models/             # SQLModel schemas + trained ML model
│   │   ├── config/             # Feature definitions, locales, model cards
│   │   └── tests/              # Backend test suite (600+ tests)
│   ├── alembic/                # Database migrations
│   └── requirements.txt
├── frontend/                   # Vue.js 3 Single Page Application
│   ├── src/
│   │   ├── components/         # Vue components (feedback, model card, charts)
│   │   ├── routes/             # Page views (patients, predictions, search)
│   │   ├── client/             # Auto-generated API client (OpenAPI)
│   │   ├── hooks/              # Composables and reusable logic
│   │   ├── locales/            # Internationalization (i18n) files
│   │   └── test/               # Vitest unit tests
│   ├── tests/                  # Playwright E2E tests
│   └── vite.config.ts
├── docker/                     # Docker Compose orchestration
│   ├── docker-compose.yml
│   └── docker-compose.override.yml
├── .github/workflows/          # CI/CD pipelines (GitHub Actions)
├── patientsData/               # Sample patient CSV data
├── scripts/                    # Utility scripts (data generation, testing, deployment)
└── SYSTEM_DESIGN.md            # Detailed architecture documentation
```

**Data Flow:**

1. **User Interface**: Frontend (Vue.js) collects patient data and sends to Backend API
2. **Preprocessing**: Backend `ModelWrapper` validates and preprocesses data via `RandomForestDatasetAdapter`
3. **Inference**: `ModelAdapter` runs prediction on the trained ML model
4. **Explanation**: Explainer computes SHAP / coefficient / LIME explanations
5. **Response**: Results (prediction + explanation) returned to frontend
6. **Persistence**: Data optionally stored in PostgreSQL for feedback and analytics

## Contributing

We welcome contributions! Please review the development setup in the respective directories:

- **Backend contributions**: See [backend/README.md](./backend/README.md)
- **Frontend contributions**: See [frontend/README.md](./frontend/README.md)

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Maintainers

- **Adelia Manafov** 
- **Artem Mozharov** 
- **Niels Kuhl**
