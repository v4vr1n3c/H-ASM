from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Minimal in-memory placeholder for demo
_ASSETS = []

@router.get("/")
def list_assets():
    return JSONResponse(content=_ASSETS)

@router.post("/mock", status_code=201)
def add_mock(asset: dict):
    _ASSETS.append(asset)
    return {"ok": True}
