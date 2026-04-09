# Local PostgreSQL with Docker

## 1. Prepare environment file

Copy `.env.example` to `.env` and adjust values if needed.

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

## 6. Useful psql connect command

```bash
docker exec -it birthday-freebies-postgres psql -U birthday_user -d birthday_freebies
```

## Notes

- Port is mapped to `localhost:5432`.
- Data is persisted in Docker volume `postgres_data`.
- Later migration to AWS RDS only requires changing `DATABASE_URL` and applying migrations.
