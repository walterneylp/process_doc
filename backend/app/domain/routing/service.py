from sqlalchemy.orm import Session

from backend.app.db import models


def route_for_classification(db: Session, tenant_id, doc_type: str, category: str, priority: str) -> dict:
    rules = (
        db.query(models.TenantRule)
        .filter(models.TenantRule.tenant_id == tenant_id, models.TenantRule.is_active == True)
        .all()
    )
    for rule in rules:
        definition = rule.definition or {}
        has_routing_keys = any(k in definition for k in ["doc_type", "category", "priority", "emails", "webhook_url"])
        if not has_routing_keys:
            continue
        if definition.get("doc_type") and definition.get("doc_type") != doc_type:
            continue
        if definition.get("category") and definition.get("category") != category:
            continue
        if definition.get("priority") and definition.get("priority") != priority:
            continue
        if has_routing_keys:
            return definition
    return {"department": "triage", "emails": [], "webhook_url": None}
