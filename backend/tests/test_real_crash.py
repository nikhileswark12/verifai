"""Manual worker-crash acceptance test for a locally running VerifAI stack.

Requires PostgreSQL, Redis, the API, and Celery beat. Starts and stops only
its own worker processes; it does not train a model or generate training data.
"""
import asyncio
import os
import subprocess
import sys
import time

import httpx

BASE_URL = os.getenv("VERIFAI_API_URL", "http://127.0.0.1:8000")
RECOVERY_TIMEOUT = int(os.getenv("VERIFAI_RECOVERY_TIMEOUT", "240"))
COMPLETION_TIMEOUT = int(os.getenv("VERIFAI_COMPLETION_TIMEOUT", "720"))


async def wait_for_status(client, job_id, predicate, timeout, description):
    deadline = time.monotonic() + timeout
    last_status = None
    while time.monotonic() < deadline:
        response = await client.get(f"/research/{job_id}")
        response.raise_for_status()
        payload = response.json()
        last_status = payload.get("status")
        if predicate(payload):
            return payload
        await asyncio.sleep(3)
    raise TimeoutError(f"Timed out waiting for {description}; last status={last_status!r}")


async def main():
    worker = None
    replacement = None
    try:
        worker = subprocess.Popen(
            [sys.executable, "-m", "celery", "-A", "app.worker.celery_app", "worker", "--pool=solo", "--loglevel=warning"],
            env=dict(os.environ, PYTHONPATH=os.getcwd()),
        )
        await asyncio.sleep(5)
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            response = await client.post("/research", json={"query": "What evidence supports the claim that Earth orbits the Sun?"})
            response.raise_for_status()
            job_id = response.json()["job_id"]
            print(f"Submitted job: {job_id}")

            await wait_for_status(client, job_id, lambda p: p.get("status") == "running", 60, "job to start")
            worker.terminate()
            worker.wait(timeout=15)
            worker = None
            print("Worker stopped; waiting for stale-job recovery.")

            await wait_for_status(
                client,
                job_id,
                lambda p: p.get("status") in {"pending", "completed", "failed"},
                RECOVERY_TIMEOUT,
                "job recovery",
            )

            replacement = subprocess.Popen(
                [sys.executable, "-m", "celery", "-A", "app.worker.celery_app", "worker", "--pool=solo", "--loglevel=warning"],
                env=dict(os.environ, PYTHONPATH=os.getcwd()),
            )
            final = await wait_for_status(
                client,
                job_id,
                lambda p: p.get("status") in {"completed", "failed"},
                COMPLETION_TIMEOUT,
                "terminal job status",
            )
            print(f"Final job status: {final.get('status')}")
            if final.get("status") != "completed":
                raise RuntimeError(f"Recovered job did not complete: {final.get('error_message')}")
    finally:
        for process in (worker, replacement):
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    asyncio.run(main())
