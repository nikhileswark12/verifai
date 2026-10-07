import os
import sys
import time
import subprocess
import signal
import asyncio
from httpx import AsyncClient

# This script must be run with the FastAPI server and Redis already running
# Uvicorn: uvicorn app.main:app --reload
# Redis: redis-server

async def main():
    print("Starting Celery worker...")
    worker = subprocess.Popen(
        ["celery", "-A", "app.worker.celery_app", "worker", "--pool=solo", "--loglevel=info"],
        env=dict(os.environ, PYTHONPATH=".")
    )
    
    print("Giving worker time to start...")
    time.sleep(5)
    
    print("Submitting research job to FastAPI...")
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/api/research", json={"query": "Why is the sky blue?"})
        job_data = response.json()
        job_id = job_data["job_id"]
        
    print(f"Job submitted: {job_id}")
    print("Waiting 10 seconds for the worker to claim and start processing...")
    time.sleep(10)
    
    print("Simulating a hard crash by killing the Celery worker...")
    worker.terminate()
    worker.wait()
    print("Worker killed.")
    
    print("Monitoring job status. It should eventually transition back to PENDING due to the sweeper.")
    async with AsyncClient(base_url="http://localhost:8000") as client:
        while True:
            response = await client.get(f"/api/research/{job_id}")
            status = response.json()["status"]
            print(f"Current status: {status}")
            if status == "pending":
                print("Job successfully recovered to PENDING!")
                break
            time.sleep(5)
            
    print("Starting a new Celery worker to resume the job...")
    new_worker = subprocess.Popen(
        ["celery", "-A", "app.worker.celery_app", "worker", "--pool=solo", "--loglevel=info"],
        env=dict(os.environ, PYTHONPATH=".")
    )
    
    print("Monitoring job until completion...")
    async with AsyncClient(base_url="http://localhost:8000") as client:
        while True:
            response = await client.get(f"/api/research/{job_id}")
            status = response.json()["status"]
            print(f"Current status: {status}")
            if status == "done":
                print("Job completed successfully!")
                break
            elif status == "error":
                print("Job errored out.")
                break
            time.sleep(5)
            
    print("Cleaning up...")
    new_worker.terminate()
    new_worker.wait()
    print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
