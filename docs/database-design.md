# Database Design

## Goals

- Store freebie entries in a relational database.
- Keep the schema simple enough for the current app, but flexible enough for future regions, more fields, and user features.
- Separate localized text from structural metadata so content can grow without changing the core model.

## Recommended Stack

- Database: PostgreSQL
- ORM: Prisma
- Backend: Node.js (current backend workspace)

## ERD

```mermaid
erDiagram
  REGIONS ||--o{ FREEBIES : contains
  FREEBIES ||--o{ FREEBIE_TEXTS : has

  REGIONS {
    uuid id PK
    string code UK
    string name
    datetime created_at
    datetime updated_at
  }

  FREEBIES {
    uuid id PK
    uuid region_id FK
    string category
    boolean is_active
    int sort_order
    datetime created_at
    datetime updated_at
  }

  FREEBIE_TEXTS {
    uuid id PK
    uuid freebie_id FK
    string locale
    string name
    string item
    string member
    string redemption_window
    string note
    datetime created_at
    datetime updated_at
  }
```

## Table Notes

### regions

Stores the region or market grouping for a set of freebies.

Suggested columns:

- `id`: primary key
- `code`: unique stable key such as `bay_area`
- `name`: display label such as `Bay Area`
- `created_at`, `updated_at`

### freebies

Stores the structural metadata for one freebie entry.

Suggested columns:

- `id`: primary key
- `region_id`: foreign key to `regions.id`
- `category`: food, drink, dessert, beauty, etc.
- `is_active`: whether the entry should be shown
- `sort_order`: optional manual ordering
- `created_at`, `updated_at`

### freebie_texts

Stores localized text for one freebie entry.

Suggested columns:

- `id`: primary key
- `freebie_id`: foreign key to `freebies.id`
- `locale`: `en`, `zh`, etc.
- `name`, `item`, `member`, `redemption_window`, `note`
- `created_at`, `updated_at`

## Why This Split Works

- Structural data stays stable while translations can grow independently.
- Adding a new language only requires inserting more rows into `freebie_texts`.
- Future filters like region, category, and active state stay easy to query.
- The schema stays compatible with the current frontend data shape.

## Implemented Constraints

- `regions.code` should be unique.
- `(freebie_id, locale)` should be unique.
- `category` is currently stored as a plain string; if we want stricter validation later, we can move it to an enum or lookup table.

## Current Indexes

- `regions.code` unique index
- `freebie_texts(freebie_id, locale)` unique index
- Foreign keys on `freebies.region_id` and `freebie_texts.freebie_id`

## Possible Future Indexes

- `freebies(region_id)`
- `freebie_texts(freebie_id)`
- `freebie_texts(locale)`
- `freebies(category)`

## Possible Next Step

The schema is already created in `backend/prisma/schema.prisma`. The next step is to:

1. Write a one-time import script from `assets/data/freebies-data.js` into the Prisma-backed database.
2. Add API endpoints for listing regions and freebies.
3. Decide whether `category` should stay a free-form string or become a stricter enum later.