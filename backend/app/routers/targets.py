from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Target
from ..schemas import TargetCreate, TargetOut

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("", response_model=list[TargetOut])
def list_targets(db: Session = Depends(get_db)):
    return db.query(Target).order_by(Target.created_at).all()


@router.post("", response_model=TargetOut)
def create_target(body: TargetCreate, db: Session = Depends(get_db)):
    if not body.git_url and not body.local_path:
        raise HTTPException(400, "provide git_url or local_path")
    target = Target(name=body.name, git_url=body.git_url, local_path=body.local_path)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(404, "target not found")
    if target.scans:
        raise HTTPException(409, "target has scans; cannot delete")
    db.delete(target)
    db.commit()
    return {"ok": True}
