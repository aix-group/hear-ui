# Contributing to HEAR-UI

Thank you for considering contributing to HEAR-UI! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork** the repository and clone your fork.
2. **Set up the development environment:**
   ```bash
   cp .env.example .env    # Configure environment variables
   ./scripts/init-dev.sh   # Initialize development environment
   ```
3. **Start the application:**
   ```bash
   docker compose -f docker/docker-compose.yml \
     -f docker/docker-compose.override.yml \
     --env-file "$PWD/.env" up -d --build
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Make your changes.
3. Run tests and linting before committing.
4. Commit with a descriptive message following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(backend): add new prediction endpoint
   fix(frontend): correct SHAP chart rendering
   docs: update API documentation
   test: add integration tests for feedback
   ```
5. Push your branch and open a Pull Request.

## Running Tests

### Backend

```bash
# Unit tests (in Docker — recommended)
docker compose -f docker/docker-compose.yml exec backend python -m pytest -v --cov=app

# Local
cd backend && pytest app/tests/ -v --cov=app --cov-report=term-missing
```

### Frontend

```bash
cd frontend
pnpm test              # Unit tests (Vitest)
pnpm test:coverage     # Coverage report
pnpm test:e2e          # E2E API tests (Playwright)
pnpm test:e2e:ui       # E2E UI tests (requires running backend)
```

## Code Quality

### Backend
- **Linter & Formatter:** [Ruff](https://docs.astral.sh/ruff/)
  ```bash
  cd backend && ruff check . && ruff format --check .
  ```
- **Type Checking:** [mypy](https://mypy-lang.org/)
  ```bash
  cd backend && mypy app/
  ```

### Frontend
- **Linter & Formatter:** [Biome](https://biomejs.dev/)
  ```bash
  cd frontend && pnpm exec biome check .
  ```

## Project Structure

| Directory | Description |
|-----------|-------------|
| `backend/` | FastAPI REST API, ML pipeline, database |
| `frontend/` | Vue.js 3 SPA (TypeScript, Vuetify) |
| `docker/` | Docker Compose orchestration |
| `docs/` | Documentation (report, user manual, system design) |
| `scripts/` | Development and data utility scripts |
| `patientsData/` | Sample patient CSV data |

## Pull Request Guidelines

- Keep PRs focused on a single change.
- Include tests for new features or bug fixes.
- Ensure all CI checks pass (lint, type check, tests).
- Update documentation if your change affects the user interface or API.

## Reporting Issues

- Use [GitHub Issues](../../issues) to report bugs or request features.
- Include steps to reproduce, expected vs. actual behavior, and environment details.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
