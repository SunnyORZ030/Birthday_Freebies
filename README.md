# 🎂 Birthday Freebies Tracker

A curated list of birthday freebies from brands in the Bay Area, including redemption requirements and validity windows.

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

Currently tracks **~30 brands**, including Starbucks, Sephora, Chipotle, Cheesecake Factory, Dutch Bros, and more.

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
	scripts/
		add_bilingual_fields.js
	CHANGELOG.md
	README.md
```

## Data Maintenance

- Runtime data is loaded from `assets/data/freebies-data.js` and `assets/data/i18n-data.js`.
- UI logic lives in `assets/scripts/app.js`.
- UI styles live in `assets/styles/main.css`.
- To regenerate bilingual fields for freebie entries, run:

```bash
node scripts/add_bilingual_fields.js
```

## Local PostgreSQL (Docker)

1. Copy env template:

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

4. Stop service:

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