# Docker Compose - Schnellreferenz

## Grundlegende Befehle

**WICHTIG:** Alle Befehle aus dem Projekt-Root (`hear-ui/`) ausführen!

### Starten (Development mit Overrides)

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d
```

### Starten mit Rebuild

```bash
docker compose -f docker/docker-compose.yml \
  -f docker/docker-compose.override.yml \
  --env-file "$PWD/.env" up -d --build
```

### Stoppen

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down
```

### Stoppen und Volumes löschen

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" down -v
```

### Logs anschauen

```bash
# Alle Services
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f

# Nur Backend
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f backend

# Nur Datenbank
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" logs -f db
```

### Status prüfen

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" ps
```

### Einzelnen Service bauen

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" build backend
```

### Befehl in Container ausführen

```bash
# Backend: pytest
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" exec backend pytest

# Datenbank: psql
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" exec db psql -U postgres -d hear_db
```

## Scripts verwenden (Empfohlen)

Alternativ können die vorbereiteten Scripts verwendet werden:

```bash
# Tests ausführen
./scripts/test.sh

# Nur Build
./scripts/build.sh

# Deploy vorbereiten
./scripts/deploy.sh
```

Die Scripts enthalten bereits die korrekten Pfade.

## Häufige Probleme

### "required variable ... is missing"

Problem: `.env` Datei wird nicht gefunden

Lösung:
- Sicherstellen, dass du im Projekt-Root bist: `cd hear-ui`
- Absoluten Pfad verwenden: `--env-file "$PWD/.env"`
- Prüfen ob `.env` existiert: `ls -la .env`

### "port is already allocated"

Problem: Container läuft bereits

Lösung:
```bash
# Alte Container stoppen
docker compose -f docker/docker-compose.yml --env-file "$PWD/.env" down

# Oder manuell
docker stop $(docker ps -q --filter name=hear-ui)
docker rm $(docker ps -aq --filter name=hear-ui)
```

### "network traefik-public not found"

Problem: Traefik-Network existiert nicht

Lösung: Für lokale Entwicklung ignorieren (nur Warning). Oder:
```bash
docker network create traefik-public
```

## Umgebungsvariablen

Die wichtigsten Variablen in `.env`:

```bash
# Docker Images
DOCKER_IMAGE_BACKEND=hear-backend
DOCKER_IMAGE_FRONTEND=hear-frontend
TAG=local

# Datenbank
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme_secure_password_here
POSTGRES_DB=hear_db

# Ports (in docker-compose.override.yml)
POSTGRES_HOST_PORT=5434  # Host-Port für PostgreSQL

# Security
SECRET_KEY=your-secret-key-here
FIRST_SUPERUSER=admin@hear-project.de
FIRST_SUPERUSER_PASSWORD=ChangeMe123!
```

## Nützliche Befehle

### Health-Check

```bash
curl http://localhost:8000/api/v1/utils/health-check/
```

### API Dokumentation öffnen

```bash
open http://localhost:8000/docs
```

### pgAdmin öffnen

```bash
open http://localhost:5051
# Login: admin@example.com / admin
```

### Datenbank-Backup

```bash
docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" exec -T db \
  pg_dump -U postgres hear_db > backup.sql
```

### Datenbank-Restore

```bash
cat backup.sql | docker compose -f docker/docker-compose.yml \
  --env-file "$PWD/.env" exec -T db \
  psql -U postgres hear_db
```
