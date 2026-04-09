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

### Compatibility
1. Backward-safe fallbacks are retained in [index.html](index.html), so missing metadata keys still degrade gracefully.
2. No data schema break for existing entries in [assets/data/freebies-data.js](assets/data/freebies-data.js).
3. Page behavior remains unchanged when the API is unavailable because the frontend falls back to static data in [assets/scripts/app.js](assets/scripts/app.js).
4. Visual behavior remains unchanged after moving styles into [assets/styles/main.css](assets/styles/main.css).
5. Data shape intentionally changed by removing deprecated `batch`, `cp`, and `dist` fields from runtime records.
6. Backend Prisma setup is now wired to the local PostgreSQL container and has a working initial migration.
7. The new API, seed flow, and frontend hydration are compatible with the existing static dataset and can be enabled incrementally.