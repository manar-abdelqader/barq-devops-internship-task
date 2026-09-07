#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_FILE="${1:?Usage: ./restore.sh backups/<file>.dump}"

case "$BACKUP_FILE" in
  "$ROOT"/*) ;;
  *) BACKUP_FILE="$ROOT/$BACKUP_FILE" ;;
esac
test -s "$BACKUP_FILE"

docker compose -f "$ROOT/docker-compose.yml" exec -T postgres \
  pg_restore -U barq_app -d barq_tasks --clean --if-exists --no-owner < "$BACKUP_FILE"
echo "[PASS] PostgreSQL restore completed: $BACKUP_FILE"
