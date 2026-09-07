#!/usr/bin/env python3
#!/usr/bin/env python3
"""Prove NGINX availability while one Flask backend is stopped and then recovered."""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8080"
STOPPED_SERVICE = "app-02"
SURVIVING_INSTANCE = "app-01"
RECOVERED_INSTANCE = "app-02"


def compose(*args, check=True):
    return subprocess.run(["docker", "compose", *args], text=True, capture_output=True,
                          check=check, timeout=60)


def request_instance():
    try:
        with urllib.request.urlopen(BASE_URL + "/instance", timeout=5) as response:
            return response.status, json.loads(response.read().decode())["instance_id"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__


def wait_for_instance(expected, attempts=20):
    for _ in range(attempts):
        status, value = request_instance()
        if status == 200 and value == expected:
            return True
        time.sleep(1)
    return False


def fail(message):
    print(f"[FAIL] {message}")
    raise RuntimeError(message)


def main():
    stopped = False
    try:
        if not wait_for_instance(SURVIVING_INSTANCE) or not wait_for_instance(RECOVERED_INSTANCE):
            fail("Both initial backends must be reachable before the failure test.")

        print(f"[INFO] Stopping {STOPPED_SERVICE}.")
        compose("stop", STOPPED_SERVICE)
        stopped = True

        successful, errors, seen = 0, 0, set()
        for _ in range(12):
            status, value = request_instance()
            if status == 200:
                successful += 1
                seen.add(value)
            else:
                errors += 1
            time.sleep(0.25)
        print(f"[INFO] During failure: successful={successful}, errors={errors}, instances={sorted(seen)}")
        if successful != 12 or errors != 0 or seen != {SURVIVING_INSTANCE}:
            fail("NGINX did not maintain error-free traffic through the surviving backend.")

        print(f"[INFO] Restoring {STOPPED_SERVICE}.")
        compose("start", STOPPED_SERVICE)
        stopped = False
        if not wait_for_instance(RECOVERED_INSTANCE):
            fail("Recovered backend did not serve /instance within 20 seconds.")
        print("[PASS] Failure tolerance and backend recovery verified.")
        return 0
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    finally:
        if stopped:
            print(f"[INFO] Cleanup: restoring {STOPPED_SERVICE}.")
            compose("start", STOPPED_SERVICE, check=False)


if __name__ == "__main__":
    sys.exit(main())
