from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import runner
from ..db import get_db
from ..models import Provider, Scan, Target
from ..schemas import ScanCreate, ScanDetail, ScanOut

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.get("", response_model=list[ScanOut])
def list_scans(db: Session = Depends(get_db)):
    return db.query(Scan).order_by(Scan.created_at.desc()).all()


@router.post("", response_model=ScanOut)
def create_scan(body: ScanCreate, db: Session = Depends(get_db)):
    target = db.get(Target, body.target_id)
    if target is None:
        raise HTTPException(404, "target not found")
    provider = db.get(Provider, body.provider_id)
    if provider is None:
        raise HTTPException(404, "provider not found")
    if not body.model_id.strip():
        raise HTTPException(400, "model_id is required")
    scan = Scan(
        target_id=body.target_id,
        provider_id=body.provider_id,
        model_id=body.model_id,
        application_id=body.application_id or f"app-{target.name}",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    runner.submit_scan(scan.id)
    return scan


@router.get("/{scan_id}", response_model=ScanDetail)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    return scan


@router.get("/{scan_id}/log", response_class=PlainTextResponse)
def get_scan_log(scan_id: int, tail: int = 400, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    path = runner.log_path_for(scan_id)
    if not path.exists():
        return ""
    lines = path.read_text(errors="replace").splitlines()
    return "\n".join(lines[-tail:])


@router.get("/{scan_id}/report", response_class=PlainTextResponse)
def get_scan_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    if not scan.report_path:
        raise HTTPException(404, "no report for this scan")
    return Path(scan.report_path).read_text(errors="replace")


@router.post("/{scan_id}/cancel", response_model=ScanOut)
def cancel_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "scan not found")
    if scan.status in ("succeeded", "failed", "canceled"):
        raise HTTPException(409, f"scan already {scan.status}")
    runner.cancel_scan(scan_id)
    scan.status = "canceled"
    db.commit()
    db.refresh(scan)
    return scan
