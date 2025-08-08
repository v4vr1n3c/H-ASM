import os
from celery import Celery
from uuid import uuid4
from app.services.discovery import run_discovery
from app.services.nuclei_runner import run_nuclei

REDIS = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("workers", broker=REDIS)

def enqueue_scan(domain, owner=None):
    scan_id = str(uuid4())
    celery_app.send_task("app.workers.tasks.worker_scan", args=[scan_id, domain, owner])
    return scan_id

@celery_app.task(name="app.workers.tasks.worker_scan")
def worker_scan(scan_id, domain, owner):
    # In a real implementation, persist scan start and states to DB.
    assets = run_discovery(domain)
    for a in assets:
        # Persist asset (omitted). For MVP, we call nuclei runner.
        run_nuclei(a.get("url"))
    return {"scan_id": scan_id, "domain": domain}
