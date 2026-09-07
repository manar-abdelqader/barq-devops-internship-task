<img src="assets/barq-logo.svg" alt="BARQ Systems" width="180">

# BARQ DevOps Internship Task

Two Flask instances run behind NGINX with PostgreSQL and Redis on isolated Docker networks. NGINX is the only public service.

## Prerequisites

Docker Desktop using Linux containers, Docker Compose v2, Python 3.12, Bash/WSL and Git. Copy the safe environment template before starting:

```bash
cp .env.example .env
# Replace CHANGE_ME in .env with the supplied assessment-lab password.
docker compose up --build -d
docker compose ps
```

The initial public URL is `http://127.0.0.1:8080`. `postgres`, `redis`, `app-01` and `app-02` do not publish host ports. Check the endpoints:

```bash
curl -i http://127.0.0.1:8080/health
curl -i http://127.0.0.1:8080/ready
curl -H 'Content-Type: application/json' -d '{"title":"Persistence proof"}' http://127.0.0.1:8080/records
curl http://127.0.0.1:8080/records
curl http://127.0.0.1:8080/counter
for i in $(seq 1 10); do curl -s http://127.0.0.1:8080/instance; echo; done
```

## Verify, failure test, persistence and backup

`validate.py` has bounded retries and exits non-zero on a failed endpoint, missing backend identity, or exposed PostgreSQL/Redis port.

```bash
python3 validate.py
python3 failure_test.py
./backup.sh
./restore.sh backups/barq_tasks_YYYYMMDDTHHMMSSZ.dump
```

For the persistence proof, create a record, recreate only the app and PostgreSQL containers without deleting volumes, then list records:

```bash
curl -H 'Content-Type: application/json' -d '{"title":"Survives recreation"}' http://127.0.0.1:8080/records
docker compose rm -sf app-01 app-02 postgres
docker compose up -d
curl http://127.0.0.1:8080/records
```

Never use `docker compose down --volumes` during this proof. To stop the lab outside the recorded challenge, use `docker compose down`; remove volumes only when intentionally discarding data.

## CI and design

GitHub Actions runs Compose syntax validation, image build, startup/readiness checks and `validate.py` on every push and pull request. A green run proves this automated two-instance scenario on a fresh runner; it does not prove the video, backup restore or production reliability. See `architecture.pdf`, `log_analysis.md`, `troubleshooting.md`, `decisions.md`, `security_review.md`, and `docs/EVIDENCE_INDEX.md`.

## Video-final configuration

During the continuous video only, change `PUBLIC_PORT` from `8080` to `8090`, add `app-03` on both application networks and update the NGINX upstream, then rerun validation adapted for three identities. Record each command, output and commit. Do not run `video_challenge.sh` before the recorded first run.

```bash
BASE_URL=http://127.0.0.1:8090 EXPECTED_INSTANCES=3 python3 validate.py
BASE_URL=http://127.0.0.1:8090 python3 failure_test.py
```
