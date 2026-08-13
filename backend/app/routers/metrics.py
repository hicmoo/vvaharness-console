from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Finding, Scan
from ..schemas import Metrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=Metrics)
def get_metrics(db: Session = Depends(get_db)):
    scans_by_status = dict(
        db.query(Scan.status, func.count(Scan.id)).group_by(Scan.status).all()
    )
    findings_by_severity = dict(
        db.query(Finding.severity, func.count(Finding.id)).group_by(Finding.severity).all()
    )
    findings_by_state = dict(
        db.query(Finding.state, func.count(Finding.id)).group_by(Finding.state).all()
    )
    top_cwes = [
        {"cwe": cwe, "count": count}
        for cwe, count in db.query(Finding.cwe, func.count(Finding.id))
        .filter(Finding.cwe.isnot(None))
        .group_by(Finding.cwe)
        .order_by(func.count(Finding.id).desc())
        .limit(10)
        .all()
    ]
    recent_scans = db.query(Scan).order_by(Scan.created_at.desc()).limit(10).all()
    return Metrics(
        total_scans=db.query(func.count(Scan.id)).scalar() or 0,
        scans_by_status=scans_by_status,
        total_findings=db.query(func.count(Finding.id)).scalar() or 0,
        findings_by_severity=findings_by_severity,
        findings_by_state=findings_by_state,
        top_cwes=top_cwes,
        recent_scans=recent_scans,
    )
