# Local PostgreSQL with Docker

## 1. Prepare environment files

Copy `.env.example` to `.env` at the repository root if you want to customize the Docker defaults.

If you are using the FastAPI backend (with Prisma tooling), make sure `backend/.env` contains the same `DATABASE_URL` value that points at this local PostgreSQL instance.

## 2. Start database

```bash
docker compose up -d
```

## 3. Check status

```bash
docker compose ps
docker compose logs postgres --tail=50
```

## 4. Stop database

```bash
docker compose down
```

## 5. Reset database data (destructive)

```bash
docker compose down -v
```

## 6. Run Prisma against this database

From `backend/`, you can apply or inspect the schema with:

```bash
npm run prisma:migrate
npm run prisma:studio
```

## 7. Useful psql connect command

```bash
docker exec -it birthday-freebies-postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Notes

- Port is mapped to `localhost:5432`.
- Data is persisted in Docker volume `postgres_data`.
- If you change the database host, user, or password, update both the root `.env` and `backend/.env` so Docker and Prisma stay in sync.
- Later migration to AWS RDS only requires changing `DATABASE_URL` and applying migrations.