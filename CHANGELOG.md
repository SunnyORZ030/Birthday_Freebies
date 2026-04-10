# Changelog

## Unreleased

### Title
Refactor metadata structure, add database-backed workflow, and improve maintainability

### Summary
1. Extracted localization and display metadata from HTML into a separate file for cleaner structure.
2. Updated script loading flow to include metadata file before app logic.
3. Added a Prisma-backed database workflow with seed/import support and a local API server.
4. Updated the frontend to hydrate from the API first, with static fallback when the backend is offline.
5. Kept runtime behavior compatible while improving readability and maintainability.
6. Added and refined inline comments across the main data, UI, and schema files.

### Changes
1. Added [assets/data/i18n-data.js](assets/data/i18n-data.js) to store:
- Region labels
- I18N dictionaries
- Shared constants
- English replacement mappings

2. Updated [index.html](index.html):
- Load [assets/data/i18n-data.js](assets/data/i18n-data.js) after [assets/data/freebies-data.js](assets/data/freebies-data.js)
- Replace large inline metadata blocks with references to window.BIRTHDAY_FREEBIES_META
- Preserve existing filtering, sorting, and rendering behavior
- Improve section comments for readability

3. Updated [scripts/add_bilingual_fields.js](scripts/add_bilingual_fields.js) and [README.md](README.md) as part of this version.

4. Reorganized runtime files into an `assets` structure:
- Moved [assets/data/freebies-data.js](assets/data/freebies-data.js) and [assets/data/i18n-data.js](assets/data/i18n-data.js) into `assets/data`.
- Updated [index.html](index.html) script paths to load data from the new location.
- Updated [scripts/add_bilingual_fields.js](scripts/add_bilingual_fields.js) to write to the new data path.

5. Extracted inline JavaScript app logic from [index.html](index.html) to [assets/scripts/app.js](assets/scripts/app.js).

6. Extracted inline CSS from [index.html](index.html) to [assets/styles/main.css](assets/styles/main.css) and switched to external stylesheet loading.

7. Removed planning-batch, CP-value, and distance-to-SJSU fields across UI, logic, and dataset:
- Removed related filter buttons and table columns from [index.html](index.html).
- Removed related filtering/rendering logic from [assets/scripts/app.js](assets/scripts/app.js).
- Removed related keys/constants from [assets/data/i18n-data.js](assets/data/i18n-data.js).
- Removed related style rules from [assets/styles/main.css](assets/styles/main.css).
- Removed deprecated fields from [assets/data/freebies-data.js](assets/data/freebies-data.js).
- Updated [scripts/add_bilingual_fields.js](scripts/add_bilingual_fields.js) so regenerated data keeps those fields removed.
- Updated [README.md](README.md) to match the new simplified data model.

8. Added local Docker PostgreSQL setup for development:
- Added [docker-compose.yml](docker-compose.yml).
- Added [docs/local-postgres-docker.md](docs/local-postgres-docker.md).
- Added [docs/database-design.md](docs/database-design.md).
- Added [.env.example](.env.example) and updated [README.md](README.md) setup instructions.
- Updated [.gitignore](.gitignore) to ignore local env files.

9. Hardened environment template values in [.env.example](.env.example) to use safe placeholders instead of directly usable credentials.

10. Initialized Prisma in [backend](backend/) for PostgreSQL-backed development:
- Installed `prisma` and `@prisma/client` in [backend/package.json](backend/package.json).
- Ran `npx prisma init --datasource-provider postgresql` to generate [backend/prisma.config.ts](backend/prisma.config.ts), [backend/prisma/schema.prisma](backend/prisma/schema.prisma), and [backend/.env](backend/.env).
- Pointed Prisma at the local Docker database through [backend/.env](backend/.env) using `DATABASE_URL`.
- Defined the initial normalized schema for `regions`, `freebies`, and `freebie_texts` in [backend/prisma/schema.prisma](backend/prisma/schema.prisma).
- Applied the first migration and generated the Prisma client output under [backend/src/generated](backend/src/generated).
- Removed the temporary Prisma smoke-test script after validation.

11. Updated [README.md](README.md) to reflect the current repository layout and backend workflow:
- Added the `backend/` Prisma workspace to the project structure.
- Documented the backend Prisma commands and `DATABASE_URL` usage.
- Clarified how the Docker PostgreSQL service and backend `.env` work together.

12. Added a lightweight database-backed API in [backend/src/server.ts](backend/src/server.ts):
- Exposed `GET /health` for local verification.
- Exposed `GET /api/freebies` to return region-grouped freebies from PostgreSQL.
- Exposed `GET /api/regions` to populate the frontend region dropdown from the database.
- Wired the server to Prisma via the PostgreSQL driver adapter.

13. Added a repeatable import/seed path for database content:
- Added [backend/prisma/seed.ts](backend/prisma/seed.ts) to read from [assets/data/freebies-data.js](assets/data/freebies-data.js).
- Added `npm run db:seed` to [backend/package.json](backend/package.json).
- Installed `@prisma/adapter-pg`, `pg`, and `tsx` for the runtime and seed scripts.
- Seed logic upserts regions, replaces each region's freebies, and writes both `zh` and `en` localized text rows.

14. Updated the frontend data flow and UI state:
- [assets/scripts/app.js](assets/scripts/app.js) now requests database data first and falls back to static data when the API is unavailable.
- Added region metadata hydration from the API so the dropdown can be driven by database content.
- Added a data-source badge in [index.html](index.html) and styled it in [assets/styles/main.css](assets/styles/main.css).
- Kept the static dataset path as a safe fallback for offline use.

15. Expanded [README.md](README.md) with a full local development workflow:
- Install backend dependencies.
- Start PostgreSQL with Docker.
- Run Prisma migrations and seed data.
- Start the backend API.
- Open the frontend and use Prisma Studio when needed.

16. Added explanatory comments to the main runtime and schema files for easier maintenance:
- [backend/src/server.ts](backend/src/server.ts)
- [assets/scripts/app.js](assets/scripts/app.js)
- [assets/data/i18n-data.js](assets/data/i18n-data.js)
- [backend/prisma/seed.ts](backend/prisma/seed.ts)
- [backend/prisma/schema.prisma](backend/prisma/schema.prisma)

17. Migrated the API runtime to Python/FastAPI and cleaned up legacy server files:
- Added FastAPI server entry at [backend/app/main.py](backend/app/main.py).
- Added Python dependencies in [backend/requirements.txt](backend/requirements.txt).
- Updated `npm run dev` to launch uvicorn through the project virtual environment.
- Removed old Node API entry files [backend/src/server.ts](backend/src/server.ts) and [backend/src/server.js](backend/src/server.js) after validating parity for `/health`, `/api/freebies`, and `/api/regions`.

18. Updated [backend/.gitignore](backend/.gitignore) for Python runtime artifacts:
- Ignored `__pycache__/` directories.
- Ignored `*.pyc` bytecode files.

19. Refactored FastAPI runtime structure for clearer data access boundaries:
- Added DB connection helper module [backend/app/db.py](backend/app/db.py).
- Added repository layer [backend/app/repositories/freebies_repository.py](backend/app/repositories/freebies_repository.py).
- Kept route handlers in [backend/app/main.py](backend/app/main.py) focused on request/response wiring.
- Added package markers [backend/app/__init__.py](backend/app/__init__.py) and [backend/app/repositories/__init__.py](backend/app/repositories/__init__.py).

20. Added explicit API contract models and standardized error envelopes:
- Added response/error schemas in [backend/app/contracts.py](backend/app/contracts.py).
- Added request validation and structured 422/500 error envelopes in [backend/app/main.py](backend/app/main.py).
- Added `region` query validation for `/api/freebies` (pattern + length constraints).

21. Added API contract documentation and linked it from README:
- Added [docs/api-contract.md](docs/api-contract.md) for stable response/error/query definitions.
- Updated [README.md](README.md) to reference the contract document and current runtime architecture.

22. Updated frontend runtime behavior to API-only data loading:
- Updated [assets/scripts/app.js](assets/scripts/app.js) to treat FastAPI as the only runtime data source.
- Removed runtime static-data fallback behavior; API failures now render explicit error states.
- Removed [assets/data/freebies-data.js](assets/data/freebies-data.js) runtime script loading from [index.html](index.html).

23. Added backend API smoke tests for route and contract stability:
- Added [backend/tests/test_api_smoke.py](backend/tests/test_api_smoke.py).
- Included validation-contract coverage for invalid `region` requests (`422` envelope).
- Added test dependencies (`pytest`, `httpx`) in [backend/requirements.txt](backend/requirements.txt).

24. Synced design and environment docs with current implementation details:
- Updated [docs/database-design.md](docs/database-design.md) to match schema/runtime/index status.
- Updated [docs/local-postgres-docker.md](docs/local-postgres-docker.md) wording and psql command behavior for env-driven credentials.

### Compatibility
1. Localization metadata fallbacks are retained in [assets/scripts/app.js](assets/scripts/app.js) through defaults on `window.BIRTHDAY_FREEBIES_META`.
2. No data schema break for existing entries in [assets/data/freebies-data.js](assets/data/freebies-data.js).
3. Frontend runtime behavior changed intentionally: when the API is unavailable, [assets/scripts/app.js](assets/scripts/app.js) now renders an error state instead of falling back to static data.
4. Visual behavior remains unchanged after moving styles into [assets/styles/main.css](assets/styles/main.css).
5. Data shape intentionally changed by removing deprecated `batch`, `cp`, and `dist` fields from runtime records.
6. Backend Prisma setup is now wired to the local PostgreSQL container and has a working initial migration.
7. Seed/import flow remains compatible with [assets/data/freebies-data.js](assets/data/freebies-data.js), but frontend runtime now requires the FastAPI API to be available.