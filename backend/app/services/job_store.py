import threading
from typing import Dict, List, Optional
from app.models import ResearchState


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, ResearchState] = {}
        self._lock = threading.Lock()

    def create(self, state: ResearchState) -> None:
        with self._lock:
            self._jobs[state.job_id] = state

    def get(self, job_id: str) -> Optional[ResearchState]:
        with self._lock:
            return self._jobs.get(job_id)

    def exists(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._jobs

    def update(self, state: ResearchState) -> None:
        with self._lock:
            if state.job_id in self._jobs:
                self._jobs[state.job_id] = state

    def delete(self, job_id: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]

    def list_jobs(self) -> List[ResearchState]:
        with self._lock:
            return list(self._jobs.values())


# Singleton instance
job_store_instance = JobStore()
