from sqlalchemy.orm import Session

from backend.app.db import models


def route_for_classification(db: Session, tenant_id, category: str, priority: str) -> dict:
    rules = (
        db.query(models.TenantRule)
        .filter(models.TenantRule.tenant_id == tenant_id, models.TenantRule.is_active == True)
        .all()
    )
    for rule in rules:
        definition = rule.definition or {}
        if definition.get("category") == category and definition.get("priority", priority) == priority:
            return definition
    return {"department": "triage", "emails": []}
