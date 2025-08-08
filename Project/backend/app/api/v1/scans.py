from fastapi import APIRouter
from pydantic import BaseModel
from app.workers.tasks import enqueue_scan

router = APIRouter()

class ScanRequest(BaseModel):
    domain: str
    owner: str | None = None

@router.post("/", status_code=202)
def create_scan(req: ScanRequest):
    scan_id = enqueue_scan(req.domain, req.owner)
    return {"scan_id": scan_id, "status": "queued"}
