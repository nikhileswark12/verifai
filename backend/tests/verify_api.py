"""
VerifAI API contract + runtime verification script.
Run: python tests/verify_api.py
"""
import json
import sys
import time

import requests

BASE = "http://127.0.0.1:8000"
PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    results.append({"test": name, "status": status, "detail": detail})
    tag = f"[{status}]"
    msg = f"  {tag} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


# ── 1. Health check ──────────────────────────────────────────────────────────
print("=== 1. HEALTH CHECK ===")
r = requests.get(f"{BASE}/health")
h = r.json()
check("HTTP 200", r.status_code == 200, f"got {r.status_code}")
check("status=healthy", h.get("status") == "healthy")
check("workflow=available", h["services"]["workflow"] == "available")
check("job_store=available", h["services"]["job_store"] == "available")
check("version present", bool(h.get("version")), h.get("version", ""))

# ── 2. POST /research ────────────────────────────────────────────────────────
print("\n=== 2. POST /research (valid) ===")
r2 = requests.post(f"{BASE}/research",
                   json={"query": "Why is climate change affecting agricultural productivity?"})
check("HTTP 202", r2.status_code == 202, f"got {r2.status_code}")
body2 = r2.json()
check("job_id present", "job_id" in body2)
check("status=accepted", body2.get("status") == "accepted")
job_id: str = body2.get("job_id", "")

# ── 3. Immediate job visibility ──────────────────────────────────────────────
print("\n=== 3. Immediate JobStore visibility ===")
time.sleep(0.2)
r3 = requests.get(f"{BASE}/research/{job_id}")
check("HTTP 200 immediately", r3.status_code == 200, f"got {r3.status_code}")
d3 = r3.json()
check("job_id matches", d3.get("job_id") == job_id)
check("agent_status present", "agent_status" in d3)
expected_agents = {"planner", "research", "verification", "contradiction", "report"}
actual_agents = set(d3.get("agent_status", {}).keys())
check("all 5 agents present", expected_agents <= actual_agents, str(actual_agents))

# ── 4. Poll to terminal state ────────────────────────────────────────────────
print("\n=== 4. Poll to terminal state (max 300s) ===")
max_wait = 300
start_t = time.time()
final_statuses: dict = {}
done_ok = False
error_ok = False
for i in range(max_wait):
    time.sleep(1)
    r4 = requests.get(f"{BASE}/research/{job_id}")
    statuses = r4.json().get("agent_status", {})
    final_statuses = statuses
    agents_done = all(v == "done" for k, v in statuses.items() if k != "orchestrator")
    any_error = any(v == "error" for v in statuses.values())
    if agents_done:
        done_ok = True
        break
    if any_error:
        error_ok = True
        break

terminal_label = "timeout" if not (done_ok or error_ok) else ("all-done" if done_ok else "error-state (expected: no credits)")
check("reached terminal state", done_ok or error_ok, terminal_label)
check("no infinite pending loop", done_ok or error_ok)
print(f"  Final: {json.dumps(final_statuses)}")

# ── 5. Result endpoint ───────────────────────────────────────────────────────
print("\n=== 5. GET /research/{job_id}/result ===")
r5 = requests.get(f"{BASE}/research/{job_id}/result")
if done_ok:
    check("HTTP 200 for completed job", r5.status_code == 200, f"got {r5.status_code}")
    rb5 = r5.json()
    check("executive_summary present", "executive_summary" in rb5)
    check("overall_assessment present", "overall_assessment" in rb5)
    check("claims present", "claims" in rb5)
else:
    check("HTTP 500 for failed job", r5.status_code == 500, f"got {r5.status_code}")
    rb5 = r5.json()
    check("error=True in body", rb5.get("error") is True)
    check("stage present", bool(rb5.get("stage")), rb5.get("stage", ""))
    check("message present", bool(rb5.get("message")))
    stage = rb5.get("stage", "")
    msg = rb5.get("message", "")[:100]
    print(f"  Error: stage={stage!r} | {msg}")

# ── 6. Input validation ──────────────────────────────────────────────────────
print("\n=== 6. Input validation ===")
rv = requests.post(f"{BASE}/research", json={"query": "hi"})
check("HTTP 422 for query < min_length", rv.status_code == 422, f"got {rv.status_code}")

rem = requests.post(f"{BASE}/research", json={})
check("HTTP 422 for missing query", rem.status_code == 422, f"got {rem.status_code}")

# ── 7. Not found ─────────────────────────────────────────────────────────────
print("\n=== 7. Not-found handling ===")
r7 = requests.get(f"{BASE}/research/00000000-0000-0000-0000-000000000000")
check("HTTP 404 for unknown job", r7.status_code == 404, f"got {r7.status_code}")
rb7 = r7.json()
check("error=True in 404", rb7.get("error") is True)
check("message in 404", bool(rb7.get("message")))

r7r = requests.get(f"{BASE}/research/00000000-0000-0000-0000-000000000000/result")
check("HTTP 404 for unknown result", r7r.status_code == 404, f"got {r7r.status_code}")

# ── 8. CORS headers ──────────────────────────────────────────────────────────
print("\n=== 8. CORS headers ===")
r8 = requests.options(f"{BASE}/research", headers={
    "Origin": "http://localhost:5173",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
})
acao = r8.headers.get("access-control-allow-origin", "")
check("CORS: allow-origin for frontend", "localhost:5173" in acao or acao == "*", f"got: {acao!r}")
acm = r8.headers.get("access-control-allow-methods", "")
check("CORS: allow-methods present", bool(acm), acm)

# ── Summary ──────────────────────────────────────────────────────────────────
print()
fails = [r for r in results if r["status"] == FAIL]
total = len(results)
print(f"=== SUMMARY: {total - len(fails)}/{total} PASS, {len(fails)} FAIL ===")
if fails:
    for f in fails:
        print(f"  FAIL: {f['test']} — {f['detail']}")
sys.exit(1 if fails else 0)
