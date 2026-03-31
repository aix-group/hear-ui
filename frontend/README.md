# HEAR-UI Frontend

> Vue.js 3 + TypeScript SPA for Cochlear Implant outcome prediction and explainability.

For project-level documentation, see the main [README](../README.md).

---

## Overview

The frontend provides a clinical web interface for:
- **Patient Management** — create, search, view, and edit patient records
- **ML Predictions** — request outcome predictions with visual probability display
- **XAI Visualizations** — SHAP feature importance charts (Plotly.js)
- **Clinical Feedback** — submit agree/disagree feedback on predictions
- **Internationalization** — German & English (i18next)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Vue.js 3 (Composition API, `<script setup>`) |
| Language | TypeScript (strict mode) |
| Build Tool | Vite |
| UI Library | Vuetify 3 (Material Design) |
| Charts | Plotly.js |
| Testing | Vitest (unit), Playwright (E2E) |
| Linting | Biome |
| API Client | Auto-generated from OpenAPI spec |
| i18n | i18next + i18next-vue |

---

## Setup

### Prerequisites

- Node.js 18+ (LTS recommended)
- pnpm (package manager)

### Quick Start

```bash
cd frontend
pnpm install
pnpm dev
# Open http://localhost:5173
```

### Environment

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## Scripts

```bash
pnpm dev              # Start dev server (hot-reload)
pnpm build            # Production build (TypeScript + Vite)
pnpm preview          # Preview production build
pnpm lint             # Lint & format check (Biome)
pnpm test             # Unit tests (Vitest)
pnpm test:coverage    # Unit tests with coverage
pnpm test:e2e         # E2E API tests (Playwright)
pnpm test:e2e:ui      # E2E UI tests (Playwright + Chromium)
pnpm generate-client  # Regenerate API client from OpenAPI
```

---

## Testing

### Unit Tests (Vitest)

```bash
pnpm test              # Run all tests
pnpm test:coverage     # With V8 coverage report
```

**Results**: 153 tests passed (20 test files)

### E2E Tests (Playwright)

```bash
pnpm test:e2e          # API-level tests
pnpm test:e2e:ui       # Browser-based UI tests (Chromium)
```

---

## Project Structure

```
frontend/
├── src/
│   ├── App.vue              # Root component
│   ├── main.ts              # Application entry point
│   ├── i18n.ts              # i18next configuration
│   ├── components/          # Reusable UI components
│   │   ├── FeedbackForm.vue   # Clinical feedback form
│   │   ├── FeedbackDialog.vue # Feedback dialog wrapper
│   │   └── ModelCard.vue      # Model information card
│   ├── routes/              # Page-level views
│   │   ├── HomePage.vue       # Landing page
│   │   ├── CreatePatients.vue # Patient creation form
│   │   ├── SearchPatients.vue # Patient search
│   │   ├── PatientDetails.vue # Patient detail view
│   │   ├── Prediction.vue     # Prediction + SHAP visualization
│   │   └── PredictionsHome.vue # Predictions overview
│   ├── client/              # Auto-generated API client (OpenAPI)
│   ├── hooks/               # Composition API hooks
│   ├── layouts/             # Layout components
│   ├── lib/                 # Shared utilities & stores
│   ├── locales/             # i18n translation files (de/en)
│   ├── plugins/             # Vuetify plugin setup
│   ├── router/              # Vue Router configuration
│   ├── styles/              # Global styles
│   └── test/                # Unit test files
├── tests/                   # Playwright E2E tests
├── public/                  # Static assets
├── biome.json               # Biome linter configuration
├── vite.config.ts           # Vite build configuration
├── vitest.config.ts         # Vitest test configuration
├── playwright.config.ts     # Playwright E2E configuration
└── tsconfig.json            # TypeScript configuration
```

---

## API Client Generation

The `src/client/` directory contains a TypeScript client auto-generated from the backend's OpenAPI schema.

```bash
# Regenerate (backend must be running)
pnpm generate-client
```

Configuration: see `openapi-ts.config.ts`

> **Note**: Do not manually edit files in `src/client/`.

---

## Docker

```bash
# From project root — starts frontend + backend + db
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d

# View frontend logs
docker compose -f docker/docker-compose.yml logs -f frontend
```

In production, the frontend is served via Nginx (see `nginx.conf`, `Dockerfile`).

---

## VS Code Extensions

Recommended for development:
- **Vue - Official** (Vue Language Features)
- **Biome** (linter/formatter)
- **TypeScript Vue Plugin**

---

## Further Documentation

- [Main README](../README.md) — Full project documentation
- [i18n Guide](frontend-i18n.md) — Internationalization setup
- [Contributing](../CONTRIBUTING.md) — Contribution guidelines

## License

MIT License — see [LICENSE](../LICENSE)
