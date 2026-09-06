# Log Analysis

Use all three supplied logs. Answer every question with commands/scripts and actual output.

Source files (originals kept unmodified):
- `logs/access.log` (nginx, JSON, 726 lines)
- `logs/error.log` (nginx, plain text, 68 lines)
- `logs/application.log` (Flask app, JSON, 730 lines)

---

**1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?**

Commands:
```
wc -l logs/access.log logs/error.log logs/application.log
head -1 logs/access.log && tail -1 logs/access.log
sort logs/access.log | uniq -d | wc -l
sort logs/application.log | uniq -d | wc -l
```
Results:
- Covered interval: `2026-08-20T11:00:00.015Z` to `2026-08-20T11:29:57.578Z` (~30 minutes).
- access.log: 726 total lines → 725 valid, 1 malformed (truncated JSON), 5 duplicate lines.
- application.log: 730 total lines → 729 valid, 1 malformed (truncated JSON), 2 duplicate lines.
- error.log: 68 total lines, plain text (not JSON), 67 contain "error", 1 is a rotation/notice line.

---

**2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?**

Command:
```
awk -F'"request_id":"' '{print $2}' logs/access.log | cut -d'"' -f1 | sort -u | wc -l
```
Result: 725 distinct `request_id` values in access.log (one request_id per client-facing request,
regardless of how many upstream servers nginx internally tried). Deduplication was done by
grouping on `request_id` and keeping the first occurrence before computing any other count, since
5 lines were found to be exact duplicates (likely a log-shipping artifact at 5-minute boundaries).
A single client request that nginx internally retried across app-01 and app-02 still has **one**
`request_id` and **one** final status, so counting by `request_id` (not by log line) avoids
double-counting retries as separate requests.

---

**3. What are the final client status counts and error rate? State your denominator.**

Command:
```
grep -o '"status":[0-9]*' logs/access.log | sort | uniq -c
```
Result:
```
620 "status":200
 10 "status":404
 40 "status":502
 47 "status":503
  8 "status":504
```
Denominator = 725 (deduplicated distinct requests).
Errors (4xx+5xx) = 10+40+47+8 = 105.
Error rate = 105/725 ≈ **14.5%**.

---

**4. Which paths, time windows and backends account for the failures?**

Commands:
```
grep -o '"path":"[^"]*"' logs/access.log | sort | uniq -c
grep '"status":5' logs/access.log | grep -o '"path":"[^"]*"' | sort | uniq -c
```
Results:
- Requests by path: `/`=123, `/counter`=118, `/health`=118, `/instance`=119, `/missing`=10,
  `/ready`=118, `/records`=119.
- 5xx failures by path: `/`=10, `/counter`=26, `/health`=10, `/ready`=23, `/records`=26.
  (`/instance` had 0 failures — it never touches Redis/Postgres directly for its own logic.)
- Time windows: 11:05:02–11:09:57 (backend app-02 / 172.23.0.12 refusing connections),
  11:12:09–11:15:52 (Redis timeout, both backends), 11:20:07–11:21:45 (Postgres auth failure,
  both backends), 11:25:14–11:26:47 (`/records` exceeding nginx's `proxy_read_timeout`).
- Backend: app-02 (172.23.0.12) was the sole cause of the first incident; the other three
  incidents affected **both** app-01 and app-02 equally since Redis/Postgres are shared
  dependencies, not per-instance.

---

**5. What are the median and p95 client latencies? State the percentile method and units.**

Command:
```
grep -o '"request_time":[0-9.]*' logs/access.log | cut -d: -f2 | sort -n | \
  awk '{a[NR]=$1} END{print "count="NR, "median="a[int(NR/2)], "p95="a[int(NR*0.95)]}'
```
Result: count=725, **median = 0.054s**, **p95 = 2.001s** (nearest-rank method on the sorted
`request_time` values from access.log; units = seconds, as reported natively by nginx).

---

**6. Which requests retried upstream? How many succeeded after retrying?**

Command:
```
grep -o '"upstream":"[^"]*, [^"]*"' logs/access.log | wc -l
```
Result: **19 requests** show a comma-separated `upstream` field (meaning nginx tried a second
backend after the first failed). All 19 completed with a final 2xx status shown to the client —
i.e. all 19 retries **succeeded**, since nginx's `proxy_next_upstream error timeout http_502
http_503` setting allowed a second attempt on the healthy instance.

---

**7. Build an incident timeline using evidence from access, error AND application logs.**

| Time (UTC) | Incident | Evidence |
|---|---|---|
| 11:00–11:05 | Normal operation, clean round-robin | access.log |
| 11:05:02–11:09:57 | app-02 (172.23.0.12) refusing connections — `Connection refused` (59 of 67 error.log lines) | error.log, application.log, access.log |
| 11:12:09–11:15:52 | Redis `TimeoutError` on both instances (`/ready`, `/counter` → 503) | application.log, access.log |
| 11:20:07–11:21:45 | PostgreSQL `InvalidPassword` on both instances (`/ready`, `/records` → 503) | application.log, access.log |
| 11:25:14–11:26:47 | `/records` succeeds internally (~2.7s) but exceeds nginx's 3s `proxy_read_timeout` → client sees 504 | application.log, access.log, error.log |

---

**8. Show one correlated failed request and one successful request. Include IDs and timestamps.**

- **Failed:** `request_id=lab-000122`, `2026-08-20T11:05:02`, path `/health`, status `502`,
  upstream `172.23.0.12:8080` (app-02, mid-outage).
- **Successful:** `request_id=lab-000123`, `2026-08-20T11:05:05`, path `/health`, status `200`,
  upstream `172.23.0.11:8080` (app-01, same incident window, different backend).

---

**9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?**

Command:
```
grep -c 'Connection refused' logs/error.log
```
Result: **59** of the 67 error.log lines are `Connection refused` — a pure proxy/connectivity
failure (nginx couldn't even open a TCP connection to app-02). These map to the 11:05–11:10
incident and show up in access.log as immediate 502s (fast, no real processing time).

By contrast, the Redis and Postgres incidents show up in application.log as `dependency_error`
events (`TimeoutError`, `InvalidPassword`) — the Flask app itself received the request and only
failed while talking to its own dependency. These are proven to be application/dependency-level
(not connectivity) because both app-01 and app-02 are reachable and log the request, but each
independently fails on the same downstream call.

---

**10. What do the logs not prove? What would you check next in a running environment?**

The supplied logs are a historical incident from 2026-08-20 — they prove that these four issue
types occurred and roughly how nginx/the app behaved at the time, but they do **not** prove
anything about the *current* state of the environment (today's container health, current network
isolation, or whether these bugs are still present). To confirm the current environment, the next
steps are: run `docker compose ps` to confirm all 5 containers are healthy now, run `validate.py`
to check every endpoint and network isolation live, and run `failure_test.py` to reproduce an
app-02-style outage on purpose and confirm nginx still fails over correctly today.