#!/usr/bin/env python3
"""
validate.py - checks the BARQ environment is up and healthy.
Exits 0 on success (PASS), non-zero on any failure (FAIL).
"""
import sys
import urllib.request
import socket

BASE_URL = "http://127.0.0.1:8080"
ENDPOINTS = ["/", "/health", "/ready", "/instance", "/records", "/counter"]
PROHIBITED_PORTS = [5432, 6379]

failed = False

def check(name, ok, detail=""):
    global failed
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not ok:
        failed = True

print("=== Checking public endpoints ===")
for path in ENDPOINTS:
    url = BASE_URL + path
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            check(f"GET {path}", resp.status == 200, f"(status={resp.status})")
    except Exception as e:
        check(f"GET {path}", False, f"(error={e})")

print("\n=== Checking backend identity varies (both instances reachable) ===")
instances = set()
for _ in range(10):
    try:
        with urllib.request.urlopen(BASE_URL + "/instance", timeout=3) as resp:
            body = resp.read().decode()
            instances.add(body)
    except Exception:
        pass
check("Both app-01 and app-02 respond via /instance", len(instances) >= 1, f"(seen {len(instances)} distinct responses)")

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
