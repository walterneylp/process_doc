from sqlalchemy.orm import Session

from backend.app.db import models


def log_event(
    db: Session,
    *,
    tenant_id,
    trace_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    payload: dict | None = None,
) -> models.AuditLog:
    item = models.AuditLog(
        tenant_id=tenant_id,
        trace_id=trace_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
