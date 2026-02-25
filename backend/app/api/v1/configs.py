from typing import Annotated

from fastapi import APIRouter, Depends
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


@router.post("/prompts")
def add_prompt(payload: PromptPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = models.TenantPrompt(tenant_id=current_user.tenant_id, name=payload.name, prompt=payload.prompt)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.post("/schemas")
def add_schema(payload: SchemaPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = models.ExtractionSchema(tenant_id=current_user.tenant_id, doc_type=payload.doc_type, schema=payload.schema)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}
