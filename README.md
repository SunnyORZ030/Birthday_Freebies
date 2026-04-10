# 🎂 Birthday Freebies Tracker

A curated list of birthday freebies from brands in the Bay Area, with an API-backed frontend that falls back to static data when the backend is offline, plus a PostgreSQL/Prisma backend for local development.

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

When the backend API is running, the page loads data from PostgreSQL first and uses the local JS dataset only as a fallback.

Currently tracks **~30 brands**, including Starbucks, Sephora, Chipotle, Cheesecake Factory, Dutch Bros, and more.

## Development Workflow

Use this sequence when you want to work on the app locally from a fresh checkout:

1. Install backend dependencies.

```bash
cd backend
npm install
pip install -r requirements.txt
```

2. Start the local PostgreSQL container from the repository root.

```bash
cd ..
docker compose up -d
```

3. Apply Prisma migrations and seed the database.

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
- The frontend will try `http://localhost:3001/api/freebies` first and fall back to the local JS dataset if the API is offline.

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
			main.py
		prisma.config.ts
		prisma/
			schema.prisma
			seed.ts
			migrations/
		src/
			generated/
		requirements.txt
		package.json
		.env
	scripts/
		add_bilingual_fields.js
	docker-compose.yml
	.env.example
	docs/
	CHANGELOG.md
	README.md
```

## Data Maintenance

- The static frontend fallback data lives in `assets/data/freebies-data.js` and `assets/data/i18n-data.js`.
- The backend API (FastAPI + psycopg) reads directly from PostgreSQL and mirrors the same region-based structure.
- UI logic lives in `assets/scripts/app.js`.
- UI styles live in `assets/styles/main.css`.
- To regenerate bilingual fields for freebie entries, run:

```bash
node scripts/add_bilingual_fields.js
```

## Backend / Prisma

- The backend workspace lives in `backend/`.
- API runtime is Python/FastAPI in `backend/app/main.py`.
- Prisma schema and migrations are in `backend/prisma/`.
- Prisma-generated client code is written to `backend/src/generated/`.
- The backend reads its connection string from `backend/.env` via `DATABASE_URL`.
- API endpoint for frontend data: `GET http://localhost:3001/api/freebies`.
- Regions endpoint: `GET http://localhost:3001/api/regions`.
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
```

Frontend loading behavior:

- Tries backend API first (`http://localhost:3001/api/freebies`).
- Falls back to static `assets/data/freebies-data.js` automatically if backend is not running.
- Shows a data-source badge in the UI so you can see whether data came from API or static source.

## Import Data Into Database

After PostgreSQL is running and your `backend/.env` has the correct `DATABASE_URL`:

```bash
cd backend
npm install
npm run prisma:migrate
npm run db:seed
```

What this does:

- Reads source data from `assets/data/freebies-data.js`.
- Upserts region rows by region code.
- Replaces existing freebies in each region and re-inserts them in the current sort order.
- Writes two localized text rows per freebie (`zh` and `en`) into `freebie_texts`.

## Development Notes

- The source of truth for seeded content is `assets/data/freebies-data.js`.
- The backend API is FastAPI-based and reads directly from PostgreSQL, while Prisma is used for schema, migrations, and seed tooling.
- Re-running `npm run db:seed` is safe; it replaces each region's freebies before reinserting them.
- If you change the Prisma schema, rerun `npm run prisma:migrate` before seeding.
- If you change generated Prisma client output, rerun `npm run prisma:generate`.
- If you add new region data, seed it first so the frontend dropdown can discover it from `/api/regions`.

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