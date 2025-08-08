from fastapi import FastAPI
from app.api.v1 import scans, assets

app = FastAPI(title="ASM Healthcare API - MVP")

app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])

@app.get("/")
def read_root():
    return {"service": "ASM Healthcare API", "version": "mvp"}
