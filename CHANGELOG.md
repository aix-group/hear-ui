# Changelog

All notable changes to the HEAR-UI project are documented in this file.

## [1.0.0] — 2026-03-31 — Final Release

### Added
- Final Report (`Report.pdf`) and User Manual (`USER_MANUAL.md`)
- Internationalization (German/English) across all UI components and backend labels
- What-if analysis tool for counterfactual exploration
- Model Card view with ethical considerations and performance metrics
- Batch CSV prediction upload endpoint
- Alternative explanation methods: LIME, coefficient-based attribution
- SHAP aligned-list response schema (features/values/attributions)
- Dependabot security monitoring

### Changed
- Backend test coverage: 75% (600+ tests across 62 files)
- Frontend test coverage: 153 tests across 20 files
- Unified prediction model to 5-fold cross-validation (N=235)

### Fixed
- Replaced deprecated `datetime.utcnow()` with `datetime.now(UTC)`
- Bilingual labels for Language & Communication boolean fields
- Scroll preservation on language switch
- Auto-translate error messages (EN/DE)

---

## [0.9.0] — 2026-03 — UI Overhaul & Polish

### Added
- Features/XAI tabs in prediction view
- Styled hyperparameter summary in model card
- Inline overlay reset buttons for What-if controls
- "Reset all" button for What-if panel
- Prediction model card screenshot

### Changed
- Improved model card rendering: metrics inline, dataset size from JSON metadata
- Frontend button styles (grey action buttons, unified sheet styles)

### Fixed
- Ruff lint: move inline imports to top-level
- Missing i18n keys for predictions, what-if, minimum fields banner

---

## [0.8.0] — 2026-02 — Testing & Coverage

### Added
- Targeted coverage tests for features, feature_catalog, predict_batch
- Backend coverage: 68% → 73% → 75%
- Frontend coverage: 95% → 96%
- CI coverage enforcement (≥69% backend gate)

### Changed
- Updated Random Forest model card to v3 (2026-02-17)
- Training data size corrected to N=235

---

## [0.7.0] — 2026-01 — Explainability & Feedback

### Added
- SHAP TreeExplainer integration with fallback strategy
- LIME explainer as alternative method
- Coefficient-based attribution
- Clinician feedback interface (agree/disagree + comment)
- Feedback persistence linked to predictions
- Configurable decision threshold endpoint

### Changed
- Prediction probabilities clipped to [0.01, 0.99]
- Top 5 features returned with each explanation

---

## [0.6.0] — 2025-12 — CI/CD Pipeline

### Added
- GitHub Actions: backend CI (9 jobs: lint, mypy, unit, integration, E2E, migration check, Docker build, Trivy scan, coverage)
- GitHub Actions: frontend CI (4 jobs: lint, unit tests, build check, E2E)
- Playwright E2E tests for frontend UI flows
- Docker multi-stage builds for backend and frontend
- Trivy container security scanning

---

## [0.5.0] — 2025-12 — Patient Management & Database

### Added
- Patient CRUD endpoints with search and validation
- PostgreSQL database with SQLModel ORM
- Alembic migration framework
- Patient data entry form with 68+ fields
- Section-based form layout with German field names
- Feature definitions JSON config with locale support

---

## [0.4.0] — 2025-11 — Frontend Migration

### Added
- Vue 3 + TypeScript + Vite frontend
- Vuetify component library
- Plotly.js for SHAP visualization
- Patient search interface
- Prediction result view

### Removed
- Legacy React UI artifacts archived

---

## [0.3.0] — 2025-11 — Core Backend

### Added
- FastAPI REST API with structured routers
- Prediction endpoint (`POST /api/v1/predict/`)
- Health check endpoint
- Random Forest model wrapper
- Feature preprocessing pipeline (39-dimensional vector)
- Docker Compose orchestration (backend, frontend, PostgreSQL, pgAdmin)

---

## [0.2.0] — 2025-11 — Project Setup

### Added
- Initial project structure (backend/frontend/docker)
- `.env.example` with documented configuration
- Backend dependency pinning
- Traefik reverse proxy configuration

---

## [0.1.0] — 2025-10 — Initial Commit

### Added
- Repository initialization
- Basic FastAPI skeleton
- Alembic migration setup
- PostgreSQL connection
