# Security and production-readiness review

1. **Secrets in an image:** copying `config/app.env` into the image exposed credentials in image layers. Removed from `Dockerfile` and `.dockerignore` now excludes it. Keep the local file ignored; use a secret manager in production.
2. **Repository token exposure:** an authenticated Git remote URL was found locally and replaced with a credential-free URL. Revoke that token and rotate any credential it could access.
3. **Host ports:** app ports were removed; only NGINX publishes the public port. Verify with `validate.py` and `docker compose ps`.
4. **Database/cache isolation:** PostgreSQL and Redis are on an internal backend network. Production should additionally restrict egress and use firewall/network policies.
5. **Container privilege:** the Flask image runs as non-root. The standard PostgreSQL, Redis and NGINX images still need image update monitoring.
6. **Image supply chain:** image digests are pinned for repeatability. Pinning does not patch vulnerabilities; scan, update and attest images in production.
7. **Single points of failure:** NGINX, PostgreSQL and Redis are single instances. Add redundant load balancers, HA database and Redis replication for production.
8. **Backup risk:** named volumes are not backups. Run `backup.sh`, test `restore.sh`, encrypt and store backups off-host in production.
9. **Observability:** JSON application/edge logs exist, but no metrics/alerts are implemented. Add health, latency, error-rate and capacity alerts.
10. **Input and proxy controls:** record titles have validation and body size is capped. Production should add TLS, rate limiting, security headers and an authentication/authorization design.
