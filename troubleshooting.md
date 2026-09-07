# Troubleshooting journal

## CI / 2026-09-07
- Symptom: GitHub Actions validation failed after roughly six minutes.
- Hypothesis: NGINX or a backend was unavailable.
- Command or test: Opened the failed `Run validation script` log in GitHub Actions.
- Actual output: `/`, `/health`, `/ready`, `/records` and `/counter` returned 200; `/instance` returned HTTP 500.
- Failed attempt and what changed thinking: adjusting only readiness timing did not fix the run, which proved startup was not the remaining fault.
- Root cause: the response helper already supplies `instance_id`, while `/instance` supplied the same key again to `jsonify`.
- Fix: `/instance` now returns only `status`; the shared response helper supplies identity.
- Retest evidence: GitHub Actions run for `a9d1b1e` passed in 39 seconds.
- Related commit: `a9d1b1e`.
- Remaining uncertainty: Docker Desktop must be running for local failure, backup and persistence evidence.

## Network boundary / 2026-09-07
- Symptom: application containers were temporarily published on host ports.
- Hypothesis: direct mappings were needed for NGINX to reach the Flask processes.
- Command or test: reviewed Compose network wiring and NGINX upstream service names.
- Actual output: Docker Compose service DNS works between shared networks; host port publication is unnecessary.
- Failed attempt and what changed thinking: direct host mappings violate the task's isolation requirement and do not affect NGINX-to-app traffic.
- Root cause: confusing host-to-container access with container-to-container access.
- Fix: remove app host mappings; NGINX connects to `app-01:8080` and `app-02:8080` on `frontend`.
- Retest evidence: validation confirms PostgreSQL and Redis host ports are closed; CI is green.
- Related commit: `203a7ca`.
- Remaining uncertainty: live failure and persistence evidence is still to be recorded.
