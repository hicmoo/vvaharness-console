from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Finding
from ..schemas import FINDING_STATES, FindingOut, FindingStateUpdate

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("", response_model=list[FindingOut])
def list_findings(
    scan_id: int | None = None,
    state: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Finding)
    if scan_id is not None:
        q = q.filter(Finding.scan_id == scan_id)
    if state is not None:
        q = q.filter(Finding.state == state)
    if severity is not None:
        q = q.filter(Finding.severity == severity)
    return q.order_by(Finding.created_at.desc()).all()


@router.patch("/{finding_id}", response_model=FindingOut)
def update_finding_state(finding_id: int, body: FindingStateUpdate, db: Session = Depends(get_db)):
    if body.state not in FINDING_STATES:
        raise HTTPException(400, f"state must be one of {FINDING_STATES}")
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(404, "finding not found")
    finding.state = body.state
    db.commit()
    db.refresh(finding)
    return finding
