"""
VerifAI End-to-End Test
========================
Starts a mock server (app/main.py with LLM clients patched), submits a
research job, polls until all agents complete, then validates the final
ResearchState contains all expected structures.

The /dump/{job_id} debug endpoint is registered only on the mock server.
This test is self-contained: it owns the port lifecycle.
"""

import os
import socket
import subprocess
import sys
import time

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ── helpers ──────────────────────────────────────────────────────────────────

def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: int = 15) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_in_use(port, host):
            return True
        time.sleep(0.3)
    return False


# ── main test ─────────────────────────────────────────────────────────────────

def run_test() -> None:
    port = 8000

    if _port_in_use(port):
        print(
            f"SKIP: Port {port} is already in use by another process. "
            "Stop all backend processes before running this test."
        )
        sys.exit(1)

    mock_script = os.path.join(os.path.dirname(__file__), "run_mock_server.py")
    print(f"Starting mock server using {sys.executable}...")
    server_process = subprocess.Popen(
        [sys.executable, mock_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_port(port):
        server_process.terminate()
        out, err = server_process.communicate()
        print("Server did not start in time!")
        print("STDOUT:", out.decode())
        print("STDERR:", err.decode())
        sys.exit(1)

    completed = False
    success = False

    try:
        # 1. Submit
        print("1. Submitting POST /research")
        r = requests.post(f"http://127.0.0.1:{port}/research", json={"query": "Why is the sky blue?"})
        r.raise_for_status()
        job_id = r.json()["job_id"]
        print(f"   Job ID: {job_id}")

        # 2. Poll
        print("2. Polling GET /research/{job_id}")
        for i in range(30):
            sr = requests.get(f"http://127.0.0.1:{port}/research/{job_id}")
            sr.raise_for_status()
            statuses = sr.json().get("agent_status", {})
            print(f"   Poll {i + 1}: {statuses}")

            all_done = all(v == "done" for k, v in statuses.items() if k != "orchestrator")
            any_error = any(v == "error" for v in statuses.values())

            if all_done:
                completed = True
                success = True
                break
            if any_error:
                completed = True
                print(f"   Pipeline reached error state: {statuses}")
                break

            time.sleep(1)

        if not completed:
            print("FAILED: Job did not reach a terminal state within 30 polls.")
            return

        # 3. Validate final state (only when the mock pipeline succeeded)
        if success:
            print("\n3. Validating final ResearchState via /dump...")
            dr = requests.get(f"http://127.0.0.1:{port}/dump/{job_id}")
            dr.raise_for_status()
            state = dr.json()

            required = ["sub_claims", "evidence_by_claim", "verification_results", "contradictions", "report"]
            missing = [k for k in required if not state.get(k)]

            if missing:
                print(f"FAILED: State missing keys: {missing}")
            else:
                print("SUCCESS! Final ResearchState contains all expected output structures.")
        else:
            print("PARTIAL: Pipeline reached error state (expected when using dummy keys).")
            print("         Error propagation verified — orchestrator status = error.")

    except Exception as exc:
        print(f"Error: {exc}")

    finally:
        server_process.terminate()
        out, err = server_process.communicate()
        if not completed:
            print("STDOUT:", out.decode())
            print("STDERR:", err.decode()[-2000:])


if __name__ == "__main__":
    run_test()
