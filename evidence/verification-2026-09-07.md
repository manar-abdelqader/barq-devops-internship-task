# Local verification — 2026-09-07

Performed with Docker Desktop (Linux containers) and `docker compose` from the repository root.

## Environment and validation

All five services were running; PostgreSQL, Redis, app-01 and app-02 reported healthy. NGINX was the only service with a host mapping: `0.0.0.0:8080->80/tcp`.

`python validate.py` passed all public endpoints (`/`, `/health`, `/ready`, `/instance`, `/records`, `/counter`), observed two distinct instance identities, and confirmed host ports 5432 and 6379 were closed.

## Failure recovery

`python failure_test.py` stopped `app-02`. During the outage it recorded `successful=12`, `errors=0`, and `instances=['app-01']`; it then restored `app-02` and reported `PASS` for recovery.

## Backup and restore

A record titled `Backup restore proof 2026-09-07` was created. `backup.sh` produced `backups/barq_tasks_20260907T101824Z.dump` (2,320 bytes). The record was deleted with a targeted SQL command, `restore.sh` restored the dump, and `GET /records` again returned that record.

## Persistence

A record titled `Survives container recreation 2026-09-07` was created. `app-01`, `app-02` and PostgreSQL were removed and recreated without removing volumes. `GET /records` then returned both proof records, including the persistence record.

These outputs are local evidence only. The required continuous video, its timestamps, the challenge receipt and the final three-instance/8090 commit remain to be recorded.
