#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$ROOT/backups"
BACKUP_FILE="${1:-$BACKUP_DIR/barq_tasks_$(date -u +%Y%m%dT%H%M%SZ).dump}"
mkdir -p "$BACKUP_DIR"

docker compose -f "$ROOT/docker-compose.yml" exec -T postgres \
  pg_dump -U barq_app -d barq_tasks --format=custom --no-owner > "$BACKUP_FILE"

test -s "$BACKUP_FILE"
echo "[PASS] PostgreSQL backup created: $BACKUP_FILE"
