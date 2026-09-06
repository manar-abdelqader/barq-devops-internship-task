#!/usr/bin/env python3
"""
validate.py - checks the BARQ environment is up and healthy.
Uses bounded retries per endpoint to tolerate slow-starting environments (e.g. CI runners).
Exits 0 on success (PASS), non-zero on any failure (FAIL).
"""
import sys
import time
import json
import urllib.request
import socket

BASE_URL = "http://127.0.0.1:8080"
ENDPOINTS = ["/", "/health", "/ready", "/instance", "/records", "/counter"]
PROHIBITED_PORTS = [5432, 6379]
MAX_RETRIES = 15
RETRY_DELAY = 2

failed = False

def check(name, ok, detail=""):
    global failed
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not ok:
        failed = True

def get_with_retry(url):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                return resp.status, resp.read().decode()
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None, last_error

print("=== Checking public endpoints (bounded retries) ===")
for path in ENDPOINTS:
    url = BASE_URL + path
    status, err = get_with_retry(url)
    check(f"GET {path}", status == 200, f"(status={status}, error={err})")

print("\n=== Checking backend identity varies (both instances reachable) ===")
instances = set()
for _ in range(10):
    status, body = get_with_retry(BASE_URL + "/instance")
    if status == 200:
        try:
            data = json.loads(body)
            instance_id = data.get("instance_id")
            if instance_id:
                instances.add(instance_id)
        except Exception:
            pass
check("Both app-01 and app-02 respond via /instance", len(instances) >= 2, f"(seen {len(instances)} distinct responses)")

print("\n=== Checking prohibited ports are NOT publicly reachable ===")
for port in PROHIBITED_PORTS:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    check(f"Port {port} should be closed to host", result != 0, f"(connect_ex={result})")

print("\n=== Summary ===")
if failed:
    print("VALIDATION FAILED")
    sys.exit(1)
else:
    print("VALIDATION PASSED")
    sys.exit(0)
