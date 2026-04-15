# 🎂 Birthday Freebies Tracker

A curated list of birthday freebies from brands in the Bay Area, with a FastAPI-driven backend on PostgreSQL and Prisma used for schema/migration/seed tooling.

## Columns

| Column | Description |
|--------|-------------|
| Store | Brand name and additional notes |
| Category | Food, Drinks/Coffee, Desserts, Beauty/Retail |
| Freebie | Description of the free item |
| Member Required? | Whether an app/account is needed and any signup conditions |
| Redemption Window | How long the offer is valid |

## How to Use

Open `index.html` in any browser. Use the filter buttons at the top to sort by category.

The page loads runtime data from PostgreSQL through FastAPI.

Currently tracks **~30 brands**, including Starbucks, Sephora, Chipotle, Cheesecake Factory, Dutch Bros, and more.

## Development Workflow

Use this sequence when you want to work on the app locally from a fresh checkout:

1. Install backend dependencies.

```bash
cd backend
npm install
# Activate your project virtual environment first, then install Python deps.
python -m pip install -r requirements.txt
```

2. Start the local PostgreSQL container from the repository root.

```bash
cd ..
docker compose up -d
```

3. Apply Prisma migrations and seed the database for initial bootstrap.

```bash
cd backend
npm run prisma:migrate
npm run db:seed
```

4. Start the backend API server.

```bash
cd backend
npm run dev
```

5. Open the frontend.

- Open [index.html](index.html) directly in a browser.
- The frontend uses `http://localhost:3001/api/freebies` as its runtime data source.

6. Optional: inspect the database in Prisma Studio.

```bash
cd backend
npm run prisma:studio
```

## Project Structure

```text
Birthday_Freebies/
	index.html
	assets/
		data/
			freebies-data.js
			i18n-data.js
		scripts/
			app.js
		styles/
			main.css
	backend/
		app/
			__init__.py
			crawlers/
				__init__.py
				starbucks_crawler.py
			db.py
			main.py
			repositories/
				__init__.py
				freebies_repository.py
				ingestion_repository.py
			services/
				__init__.py
				freebies_service.py
				starbucks_ingestion_service.py
		prisma.config.ts
		prisma/
			schema.prisma
			seed.ts
			migrations/
		scripts/
			ingest_starbucks.py
		src/
			generated/
		tests/
			test_api_integration_read.py
			test_api_smoke.py
			test_ingestion_starbucks.py
			test_api_write.py
		requirements.txt
		package.json
		.env
	scripts/
		sync_freebies_api.js
	docker-compose.yml
	.env.example
	docs/
	CHANGELOG.md
	README.md
```

## Data Maintenance

- The frontend runtime data source is FastAPI; the static data files under `assets/data/` are now legacy content sources, not page runtime inputs.
- The backend API (FastAPI + psycopg) reads directly from PostgreSQL.
- Day-to-day content changes should go through the FastAPI write endpoints, `npm run sync:freebies`, or crawler ingestion jobs.
- Crawler ingestion uses a stage-and-promote flow: crawl -> normalize payload -> upsert staging row -> promote changed records.
- UI logic lives in `assets/scripts/app.js`.
- UI styles live in `assets/styles/main.css`.

## Backend / Prisma

- The backend workspace lives in `backend/`.
- API runtime is Python/FastAPI in `backend/app/main.py`.
- DB connection and normalization helpers are in `backend/app/db.py`.
- SQL query/data-mapping repository functions are in `backend/app/repositories/freebies_repository.py`.
- Service-level business rules (validation, ordering, locale fallback) are in `backend/app/services/freebies_service.py`.
- Crawler parsing logic lives in `backend/app/crawlers/`.
- Ingestion persistence helpers for staging/mapping tables are in `backend/app/repositories/ingestion_repository.py`.
- Starbucks PoC ingestion orchestration lives in `backend/app/services/starbucks_ingestion_service.py`.
- Prisma schema and migrations are in `backend/prisma/`.
- Prisma-generated client code is written to `backend/src/generated/`.
- The backend reads its connection string from `backend/.env` via `DATABASE_URL`.
- API endpoint for frontend data: `GET http://localhost:3001/api/freebies`.
- Regions endpoint: `GET http://localhost:3001/api/regions`.
- Write endpoints: `POST /api/freebies`, `PUT /api/freebies/{freebie_id}`, `DELETE /api/freebies/{freebie_id}`.
- Stable API contract document: `docs/api-contract.md`.
- Useful commands:

```bash
cd backend
# FastAPI runtime
npm run dev
# Prisma / database tooling
npm run prisma:generate
npm run prisma:migrate
npm run db:seed
npm run prisma:studio
# API smoke tests
python -m pytest -q
# Sync source data through the write API
npm run sync:freebies -- --dry-run
# Run Starbucks crawler PoC (crawl -> staging -> promote)
npm run ingest:starbucks
```

Frontend loading behavior:

- Uses backend API (`http://localhost:3001/api/freebies`) as the runtime data source.
- Shows a data-source badge in the UI so you can see whether data came from API or whether the API is unavailable.

Backend tests:

- Read-contract smoke tests live in `backend/tests/test_api_smoke.py`.
- Write-flow tests live in `backend/tests/test_api_write.py`.
- DB-backed read integration tests live in `backend/tests/test_api_integration_read.py`.
- Crawler ingestion idempotency test lives in `backend/tests/test_ingestion_starbucks.py`.

## Import Data Into Database

After PostgreSQL is running and your `backend/.env` has the correct `DATABASE_URL`:

```bash
cd backend
npm install
npm run prisma:migrate
npm run db:seed
```

Use `db:seed` for initial database bootstrap or a full reset.

To sync the current source data through the FastAPI write endpoint, run:

```bash
cd backend
npm run sync:freebies
```

Useful variants:

```bash
cd backend
npm run sync:freebies -- --dry-run
npm run sync:freebies -- --region bay_area --limit 1
```

What this does:

- Reads source data from `assets/data/freebies-data.js`.
- Normalizes source entries into the FastAPI write contract.
- Posts each freebie to `POST /api/freebies`.
- Lets you dry-run or filter to one region while keeping the same payload shape a future crawler can use.

## Development Notes

- The source of truth for active runtime data is PostgreSQL behind FastAPI.
- `assets/data/freebies-data.js` is the current import source for seed and sync workflows, not the runtime frontend source.
- The backend API is FastAPI-based and reads directly from PostgreSQL, while Prisma is used for schema, migrations, and bootstrap tooling.
- Re-running `npm run db:seed` is safe for resets, but normal content maintenance should use the write API or `npm run sync:freebies`.
- Starbucks crawler PoC can be run with `npm run ingest:starbucks`; unchanged payload reruns are idempotent and do not duplicate promoted freebies.
- Ingestion staging and mapping tables (`crawler_staging_freebies`, `crawler_promoted_mappings`) track source payloads and promotion lineage.
- If you change the Prisma schema, rerun `npm run prisma:migrate` before seeding.
- If you change generated Prisma client output, rerun `npm run prisma:generate`.
- If you add new region data, seed it first for bootstrap or sync it through the write API so the frontend dropdown can discover it from `/api/regions`.

## Local PostgreSQL (Docker)

1. Copy env template for the Docker database if you have not already:

```bash
cp .env.example .env
```

2. Start PostgreSQL:

```bash
docker compose up -d
```

3. Verify service:

```bash
docker compose ps
```

4. If you are working in `backend/`, make sure `DATABASE_URL` in `backend/.env` points at the same local PostgreSQL instance.

5. Stop service:

```bash
docker compose down
```

Detailed setup guide: [docs/local-postgres-docker.md](docs/local-postgres-docker.md)

## Roadmap / Planned Features

- [ ] **Add/edit entries in UI** — Provide a form-based interface to add or edit freebies without modifying source code.
- [ ] **Signup deadline calculator** — Let users enter their birthday and automatically compute the latest possible signup date for each brand (e.g., 7/14/30 days before birthday requirements).
- [ ] **Multi-region support** — Expand coverage to additional locations and allow users to filter or switch between different regions.
- [ ] **Personal redemption tracker** — Allow users to mark offers as redeemed and track progress across their birthday month.
- [ ] **Reminder notifications** — Notify users before key deadlines (signup cutoff or redemption expiry), such as via browser notifications.
- [ ] **Export options** — Export filtered results to CSV or a print-friendly view for offline planning.
- [ ] **Automated data updates** — Automatically scrape each brand's official website to keep offer details, eligibility requirements, and validity windows up to date.

## Data Source

Based on each brand's official Rewards program terms, last updated March 2026.

## Disclaimer

Offer terms, eligibility requirements, and validity windows are subject to change at any time without notice. The information in this tracker is provided for reference only. Always verify the latest details directly with each brand's official website or app before visiting.