from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models

router = APIRouter(prefix="/configs", tags=["configs"])


class RulePayload(BaseModel):
    rule_name: str
    definition: dict


class PromptPayload(BaseModel):
    name: str
    prompt: str


class SchemaPayload(BaseModel):
    doc_type: str
    schema: dict


class RoutePayload(BaseModel):
    doc_type: str | None = None
    category: str | None = None
    priority: str | None = None
    department: str | None = None
    emails: list[str] = []
    webhook_url: str | None = None
    rule_name: str | None = None


@router.get("/rules")
def list_rules(
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
    active_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
):
    query = db.query(models.TenantRule).filter(models.TenantRule.tenant_id == current_user.tenant_id)
    if active_only:
        query = query.filter(models.TenantRule.is_active == True)

    items = query.order_by(models.TenantRule.created_at.desc(), models.TenantRule.id.desc()).limit(limit).all()
    return [
        {
            "id": i.id,
            "rule_name": i.rule_name,
            "definition": i.definition,
            "is_active": i.is_active,
            "created_at": i.created_at,
        }
        for i in items
    ]


@router.post("/rules")
def add_rule(payload: RulePayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = models.TenantRule(
        tenant_id=current_user.tenant_id,
        rule_name=payload.rule_name,
        definition=payload.definition,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.get("/prompts")
def list_prompts(
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
    active_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
):
    query = db.query(models.TenantPrompt).filter(models.TenantPrompt.tenant_id == current_user.tenant_id)
    if active_only:
        query = query.filter(models.TenantPrompt.is_active == True)

    items = query.order_by(models.TenantPrompt.created_at.desc(), models.TenantPrompt.id.desc()).limit(limit).all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "prompt": i.prompt,
            "is_active": i.is_active,
            "created_at": i.created_at,
        }
        for i in items
    ]


@router.post("/prompts")
def add_prompt(payload: PromptPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = models.TenantPrompt(tenant_id=current_user.tenant_id, name=payload.name, prompt=payload.prompt)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.get("/schemas")
def list_schemas(
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
    active_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
):
    query = db.query(models.ExtractionSchema).filter(models.ExtractionSchema.tenant_id == current_user.tenant_id)
    if active_only:
        query = query.filter(models.ExtractionSchema.is_active == True)

    items = query.order_by(models.ExtractionSchema.created_at.desc(), models.ExtractionSchema.id.desc()).limit(limit).all()
    return [
        {
            "id": i.id,
            "doc_type": i.doc_type,
            "schema": i.schema,
            "is_active": i.is_active,
            "created_at": i.created_at,
        }
        for i in items
    ]


@router.post("/schemas")
def add_schema(payload: SchemaPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = models.ExtractionSchema(tenant_id=current_user.tenant_id, doc_type=payload.doc_type, schema=payload.schema)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.get("/routes")
def list_routes(
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
    active_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
):
    query = (
        db.query(models.TenantRule)
        .filter(models.TenantRule.tenant_id == current_user.tenant_id)
        .filter(models.TenantRule.rule_name.like("route:%"))
    )
    if active_only:
        query = query.filter(models.TenantRule.is_active == True)
    items = query.order_by(models.TenantRule.created_at.desc(), models.TenantRule.id.desc()).limit(limit).all()
    return [
        {
            "id": i.id,
            "rule_name": i.rule_name,
            "definition": i.definition,
            "is_active": i.is_active,
            "created_at": i.created_at,
        }
        for i in items
    ]


@router.post("/routes")
def add_route(payload: RoutePayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    default_name = f"route:{payload.doc_type or '*'}:{payload.category or '*'}:{payload.priority or '*'}"
    definition = {
        "doc_type": payload.doc_type,
        "category": payload.category,
        "priority": payload.priority,
        "department": payload.department,
        "emails": payload.emails or [],
        "webhook_url": payload.webhook_url,
    }
    item = models.TenantRule(
        tenant_id=current_user.tenant_id,
        rule_name=payload.rule_name or default_name,
        definition=definition,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}
