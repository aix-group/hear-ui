# frontend/src

Source code for the HEAR-UI frontend application (Vue.js 3 + TypeScript).

## Development

- See [frontend/README.md](../README.md) for full setup instructions.
- From the `frontend` directory:
  - Install dependencies: `pnpm install`
  - Start dev server: `pnpm dev` and open `http://localhost:5173`

## Generate / Update API Client

When the backend OpenAPI schema changes, regenerate the client:

```bash
# From project root
./scripts/generate-client.sh

# Or from frontend/
pnpm generate-client
```

Ensure the backend is running so that the latest `openapi.json` is available.

## Other Commands

```bash
pnpm build           # Production build
pnpm test            # Unit tests (Vitest)
pnpm test:coverage   # Tests with coverage
pnpm lint            # Lint & format (Biome)
```

## Notes

- `client/` is auto-generated code — avoid manual edits.
- `components/` — reusable Vue components (FeedbackForm, ModelCard, etc.)
- `routes/` — page-level views (HomePage, Prediction, SearchPatients, etc.)
- `lib/` — shared API utilities and state management
- `locales/` — i18n translation files (de/en)
