# Config directory

This directory holds editable metadata used by the backend (and, indirectly, the UI) to describe
model features, labels, and section grouping.

## files overview

- `features.yaml`
  - Optional, editable feature catalog used by the backend **utils** endpoints.
  - Loaded by `backend/app/core/feature_config.py` via `load_feature_config()`.
  - If the file is missing or invalid, the backend falls back to hard‑coded defaults in
    `backend/app/api/routes/utils.py`.

- `feature_definitions.json`
  - Canonical feature definitions used by the **features** endpoints
    (`/api/v1/features/definitions`, `/api/v1/features/locales/{locale}`).
  - This file powers the dynamic patient form in the frontend.

- `feature_locales/*.json`
  - Localized labels for feature **normalized** names (e.g. `de.json`, `en.json`).

- `section_locales/*.json`
  - Localized section labels used to group the dynamic form.

## feature_definitions.json usage and updates

`feature_definitions.json` is the source of truth for the dynamic patient form.
The backend loads it in `backend/app/core/feature_catalog.py` and serves it via:

- `GET /api/v1/features/definitions`
- `GET /api/v1/features/locales/{locale}`

Note: `load_feature_definitions()` is cached with `lru_cache`, so changes require
a backend restart to take effect.

### schema (per feature entry)

Top-level structure:

```json
{ "features": [ { ... }, { ... } ] }
```

Common fields in each feature:

- `raw` (string, required)
  - The raw feature name used by the model input (German column name).
- `normalized` (string, required)
  - Stable, code-friendly key used by the frontend and locales.
- `description` (string)
  - Human description; used as a fallback label.
- `type` (string)
  - Current types in this file: `string`, `number`, `enum`, `boolean`.
- `required` (boolean)
  - Whether the form treats the field as required.
- `validation` (object)
  - Validation rules. Common `validation.type` values used here:
    `string_min_length`, `string_required`, `string_optional`,
    `enum_one_of`, `enum_one_of_optional`, `number_range`, `boolean`.
- `options` (array)
  - For enums. Each option supports:
    - `value` (string)
    - `labels` (object with `de`/`en`)
    - `role` (optional, e.g. `true`/`false` for checkbox mapping)
    - `is_other` (optional, marks an option that reveals an `other_field`)
- `section` (string)
  - Logical grouping for the form. Labels are translated via `section_locales/*.json`.
- `input_type` (string)
  - UI hint (e.g. `number`) for the frontend component.
- `multiple` (boolean)
  - Enables multi-select (rendered as a combobox in the UI).
- `other_field` (string)
  - Name of another `normalized` field used when an "other" option is selected.
- `ui_only` (boolean)
  - Field exists only in the UI (not sent in `input_features`).
- `encoding` (object)
  - Optional mapping notes for boolean values (stored as `Vorhanden/Keine`, etc.).

### update workflow

1) Edit `backend/app/config/feature_definitions.json`.
   - Keep `raw` and `normalized` unique.
   - If you add new `normalized` keys, add labels in `feature_locales/*.json`.
   - If you add new `section` values, add translations in `section_locales/*.json`.

2) Restart the backend (definitions are cached).

3) Reload the frontend to pick up the new definitions.

### notes on UI behavior

- `type: boolean` renders as a checkbox.
- `enum` + `options` renders as a select; `multiple: true` renders as multi-select.
- `other_field` + `is_other` shows a free-text input when the "other" option is chosen.
