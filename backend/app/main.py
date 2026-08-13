from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine
from .models import Base
from .routers import findings, metrics, providers, scans, targets

Base.metadata.create_all(engine)

app = FastAPI(title="vvaharness console")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers.router)
app.include_router(targets.router)
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(metrics.router)


@app.get("/api/health")
def health():
    return {"ok": True}
