from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.domain.billing.service import seed_plans
from backend.app.db import models
from backend.app.db.session import get_db

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantPayload(BaseModel):
    name: str
    slug: str


@router.post("")
def create_tenant(payload: TenantPayload, db: Annotated[Session, Depends(get_db)]):
    seed_plans(db)
    tenant = models.Tenant(name=payload.name, slug=payload.slug)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"id": str(tenant.id), "name": tenant.name, "slug": tenant.slug}


@router.get("")
def list_tenants(db: Annotated[Session, Depends(get_db)]):
    items = db.query(models.Tenant).all()
    return [{"id": str(t.id), "name": t.name, "slug": t.slug} for t in items]
