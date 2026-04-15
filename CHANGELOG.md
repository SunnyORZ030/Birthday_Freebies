# Changelog

## Unreleased

### Title
Stabilize FastAPI data platform, expand contract testing, and introduce crawler-based ingestion

### Summary
1. Completed migration to a FastAPI-first runtime with PostgreSQL as the single runtime source of truth.
2. Standardized and validated API contracts with expanded DB-backed integration tests for shape, grouping, sorting, and error envelopes.
3. Upgraded core Python runtime dependencies to current stable versions and revalidated full test stability.
4. Added a Starbucks crawler PoC ingestion pipeline with stage-and-promote architecture.
5. Implemented idempotent promotion logic using source-key mapping and payload hashing to prevent duplicate writes on reruns.
6. Synced docs and code comments across README, database design, and ingestion modules for clearer maintenance and onboarding.

### Changes
#### Platform

- Extracted metadata/config from HTML to [assets/data/i18n-data.js](assets/data/i18n-data.js), moved runtime JS/CSS to [assets/scripts/app.js](assets/scripts/app.js) and [assets/styles/main.css](assets/styles/main.css), and reorganized static assets under `assets/`.
- Removed deprecated planning fields (`batch`, `cp`, `dist`) across UI, data model, rendering, and styling.
- Added local PostgreSQL Docker workflow and hardened env templates via [docker-compose.yml](docker-compose.yml), [.env.example](.env.example), and supporting docs.
- Initialized Prisma in [backend](backend/) with normalized schema (`regions`, `freebies`, `freebie_texts`), migrations, generated client, and seed flow.
- Migrated backend runtime from legacy Node API to Python/FastAPI in [backend/app/main.py](backend/app/main.py), including routing parity for `/health`, `/api/freebies`, and `/api/regions`.
- Refactored backend layering with dedicated DB helper, repositories, services, package markers, and standardized error/contract models in [backend/app/contracts.py](backend/app/contracts.py).
- Enforced API-only frontend runtime loading by removing static-data runtime fallback and surfacing explicit API-unavailable UI states.
- Upgraded core backend runtime dependencies in [backend/requirements.txt](backend/requirements.txt): `fastapi 0.135.3`, `uvicorn 0.44.0`, `psycopg[binary] 3.3.3`, `python-dotenv 1.2.2`.

#### Testing

- Added API smoke coverage in [backend/tests/test_api_smoke.py](backend/tests/test_api_smoke.py) for route stability and validation envelopes.
- Expanded DB-backed integration coverage in [backend/tests/test_api_integration_read.py](backend/tests/test_api_integration_read.py):
	- response-shape contract checks,
	- multi-region grouping and sort behavior,
	- schema-level key assertions,
	- invalid-region 422 envelope checks,
	- empty-result contract checks.
- Added write-flow coverage in [backend/tests/test_api_write.py](backend/tests/test_api_write.py).
- Added crawler-ingestion idempotency coverage in [backend/tests/test_ingestion_starbucks.py](backend/tests/test_ingestion_starbucks.py) to verify reruns do not duplicate promoted freebies.
- Revalidated post-upgrade stability with full backend suite green (`16 passed`).

#### Ingestion

- Added Starbucks crawler PoC parser in [backend/app/crawlers/starbucks_crawler.py](backend/app/crawlers/starbucks_crawler.py).
- Added ingestion repository in [backend/app/repositories/ingestion_repository.py](backend/app/repositories/ingestion_repository.py) with stage/mapping upsert helpers.
- Added orchestration service in [backend/app/services/starbucks_ingestion_service.py](backend/app/services/starbucks_ingestion_service.py) implementing:
	- normalize-to-contract payload generation,
	- content-hash based change detection,
	- idempotent promote logic (create vs update),
	- mapping updates and staging promotion markers.
- Added schema + migration for ingestion tracking tables:
	- `crawler_staging_freebies`
	- `crawler_promoted_mappings`
	in [backend/prisma/schema.prisma](backend/prisma/schema.prisma) and [backend/prisma/migrations/20260410153000_add_crawler_staging_and_mappings/migration.sql](backend/prisma/migrations/20260410153000_add_crawler_staging_and_mappings/migration.sql).
- Added runnable ingestion entrypoint [backend/scripts/ingest_starbucks.py](backend/scripts/ingest_starbucks.py) and command `npm run ingest:starbucks` in [backend/package.json](backend/package.json).

#### Docs

- Updated [README.md](README.md) throughout for architecture, setup, command workflow, test inventory, and ingestion operations.
- Added and maintained API contract reference in [docs/api-contract.md](docs/api-contract.md).
- Updated [docs/database-design.md](docs/database-design.md) to include crawler staging/mapping models, constraints, indexes, and stage-and-promote flow.
- Updated [docs/local-postgres-docker.md](docs/local-postgres-docker.md) for env-driven local DB operations.
- Added focused maintainability comments across runtime, schema, ingestion modules, and tests.

### Compatibility
1. Localization metadata fallbacks are retained in [assets/scripts/app.js](assets/scripts/app.js) through defaults on `window.BIRTHDAY_FREEBIES_META`.
2. No data schema break for existing entries in [assets/data/freebies-data.js](assets/data/freebies-data.js).
3. Frontend runtime behavior changed intentionally: when the API is unavailable, [assets/scripts/app.js](assets/scripts/app.js) now renders an error state instead of falling back to static data.
4. Visual behavior remains unchanged after moving styles into [assets/styles/main.css](assets/styles/main.css).
5. Data shape intentionally changed by removing deprecated `batch`, `cp`, and `dist` fields from runtime records.
6. Backend Prisma setup is now wired to the local PostgreSQL container and has a working initial migration.
7. Seed/import flow remains compatible with [assets/data/freebies-data.js](assets/data/freebies-data.js), and frontend runtime now requires the FastAPI API to be available.
8. Backend runtime dependency baselines were refreshed in [backend/requirements.txt](backend/requirements.txt) without changing API contract behavior.
9. Crawler ingestion and staging/mapping additions are internal data-pipeline changes and do not alter the public REST API contract.