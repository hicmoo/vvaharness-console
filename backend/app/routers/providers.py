from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import providers as provider_api
from ..crypto import decrypt, encrypt
from ..db import get_db
from ..models import Provider
from ..schemas import PROVIDER_KINDS, ModelInfo, ProviderCreate, ProviderOut

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    return db.query(Provider).order_by(Provider.created_at).all()


@router.post("", response_model=ProviderOut)
def create_provider(body: ProviderCreate, db: Session = Depends(get_db)):
    if body.kind not in PROVIDER_KINDS:
        raise HTTPException(400, f"kind must be one of {PROVIDER_KINDS}")
    if body.kind == "custom":
        if not (body.base_url or "").strip():
            raise HTTPException(400, "base_url is required for custom providers")
    elif not body.api_key.strip():
        raise HTTPException(400, "api_key is required")
    verified = provider_api.verify_key(body.kind, body.api_key, body.base_url)
    provider = Provider(
        kind=body.kind,
        name=body.name,
        encrypted_key=encrypt(body.api_key),
        base_url=body.base_url,
        status="verified" if verified else "invalid",
        last_verified_at=datetime.now(UTC) if verified else None,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.post("/{provider_id}/verify", response_model=ProviderOut)
def verify_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(404, "provider not found")
    ok = provider_api.verify_key(provider.kind, decrypt(provider.encrypted_key), provider.base_url)
    provider.status = "verified" if ok else "invalid"
    if ok:
        provider.last_verified_at = datetime.now(UTC)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/{provider_id}/models", response_model=list[ModelInfo])
def list_models(provider_id: int, db: Session = Depends(get_db)):
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(404, "provider not found")
    try:
        return provider_api.list_models(
            provider.kind, decrypt(provider.encrypted_key), provider.base_url
        )
    except provider_api.ProviderError as e:
        raise HTTPException(502, str(e)) from e


@router.delete("/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(404, "provider not found")
    if provider.scans:
        raise HTTPException(409, "provider has scans; cannot delete")
    db.delete(provider)
    db.commit()
    return {"ok": True}
