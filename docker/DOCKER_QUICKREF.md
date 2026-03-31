# Docker Compose — Quick Reference

## Basic Commands

**IMPORTANT:** Run all commands from the project root (`hear-ui/`)!

### Start (Development with Overrides)

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d
```

### Start with Rebuild

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build
```

### Stop

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down
```

### Stop and Remove Volumes

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down -v
```

### View Logs

```bash
# All services
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f

# Backend only
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f backend

# Database only
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f db
```

## Service Access (Development)

| Service   | URL                          | Notes                            |
|-----------|------------------------------|----------------------------------|
| Frontend  | http://localhost:5173        | Vite dev proxy                   |
| Backend   | http://localhost:8000        | FastAPI (Swagger at `/docs`)     |
| Database  | `localhost:5434`             | PostgreSQL (override port)       |
| pgAdmin   | http://localhost:5051        | Credentials from `.env`          |

## Database

### Connect via psql

```bash
psql -h localhost -p 5434 -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

### Run Migrations

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" exec backend alembic -c /app/alembic.ini upgrade head
```

### Reset Database (Destructive!)

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down -v
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d
```

## Troubleshooting

### Problem: "port is already allocated"

Another process is using the port. Find and stop it:

```bash
# Find what's using port 5434
lsof -i :5434

# Or change the port in .env
POSTGRES_HOST_PORT=5435
```

### Problem: Backend cannot connect to database

1. Make sure `.env` exists: `ls -la .env`
2. Verify database is healthy: `docker compose ... ps`
3. Check database logs: `docker compose ... logs db`

### Problem: Containers won't start

```bash
# Remove all containers and rebuild
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" down
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build
```

### Problem: Stale images

```bash
# Remove unused images
docker image prune -f

# Force rebuild without cache
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" build --no-cache
```
