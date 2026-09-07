# Technical decisions

## Container base image and user
- Choice: pinned `python:3.12-slim-bookworm`, running the app as UID 10001.
- Why: smaller, reproducible base and no root application process.
- Alternative/trade-off: Alpine is smaller but can complicate Python wheels; pin updates require an intentional maintenance cycle.
- Evidence: `Dockerfile`, commit `c7bea95`.
- Production: rebuild on vulnerability advisories and sign/scan images.

## Network boundary
- Choice: NGINX + apps use `frontend`; apps + PostgreSQL + Redis use internal `backend`.
- Why: only NGINX can be reached from the host; apps use service DNS instead of IPs.
- Alternative/trade-off: a single network is simpler but exposes dependencies to the edge.
- Evidence: `docker-compose.yml`, `validate.py` closed-port checks.
- Production: apply firewall/network-policy controls as well.

## Health and readiness
- Choice: `/health` checks process liveness; `/ready` checks real PostgreSQL and Redis operations.
- Why: an alive Flask process is not necessarily able to serve data.
- Trade-off: dependency checks add short request latency; connection/statement timeouts cap it.
- Evidence: `app/server.py`, CI readiness step.

## Availability behavior
- Choice: two backend instances, NGINX failover for connection errors/timeouts/502/503, bounded retry settings.
- Why: a single app failure should not take the public endpoint down.
- Trade-off: retries can add latency and are suitable only for safe requests; `failure_test.py` measures the behavior.
- Evidence: `nginx/nginx.conf`, `failure_test.py`.

## Stateful storage
- Choice: named PostgreSQL and Redis volumes; Redis AOF enabled.
- Why: data survives container recreation while preserving a clear cleanup boundary.
- Trade-off: volumes are local single-host storage and require backup/restore tests.
- Evidence: `docker-compose.yml`, `backup.sh`, `restore.sh`.

## Resource and restart settings
- Choice: `unless-stopped`, conservative CPU/memory limits and bounded health retries.
- Why: limits prevent one lab service from consuming the host; restart helps transient process exits.
- Trade-off: Compose `deploy.resources` support varies by runtime; verify on the target engine.
- Evidence: `docker-compose.yml`.
