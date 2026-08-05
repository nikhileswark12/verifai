from app.services.job_store import JobStore, job_store_instance


def get_job_store() -> JobStore:
    return job_store_instance
