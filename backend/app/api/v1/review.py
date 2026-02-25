from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.workers.tasks import process_document

router = APIRouter(prefix="/review", tags=["review"])


class ReviewDecisionPayload(BaseModel):
    category: str | None = None
    department: str | None = None
    priority: str | None = None
    reason: str | None = None
    extraction: dict | None = None


@router.get("")
def review_queue(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = (
        db.query(models.Document)
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.needs_review == True)
        .all()
    )
    result = []
    for item in items:
        classification = (
            db.query(models.Classification)
            .filter(models.Classification.document_id == item.id)
            .order_by(models.Classification.created_at.desc())
            .first()
        )
        extraction = (
            db.query(models.Extraction)
            .filter(models.Extraction.document_id == item.id)
            .order_by(models.Extraction.created_at.desc())
            .first()
        )
        dead_letter = (
            db.query(models.DeadLetter)
            .filter(models.DeadLetter.entity_type == "document", models.DeadLetter.entity_id == str(item.id))
            .order_by(models.DeadLetter.created_at.desc())
            .first()
        )
        result.append(
            {
                "id": str(item.id),
                "status": item.status,
                "trace_id": item.trace_id,
                "doc_type": item.doc_type,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "classification": {
                    "category": classification.category,
                    "department": classification.department,
                    "priority": classification.priority,
                    "confidence": float(classification.confidence),
                    "reason": classification.reason,
                    "source": classification.source,
                }
                if classification
                else None,
                "extraction": extraction.data if extraction else {},
                "review_reason": dead_letter.reason if dead_letter else None,
            }
        )
    return result


@router.post("/{document_id}/approve")
def approve_review(
    document_id: str,
    payload: ReviewDecisionPayload,
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
):
    item = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.tenant_id == current_user.tenant_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="document_not_found")

    existing_cls = (
        db.query(models.Classification)
        .filter(models.Classification.document_id == item.id)
        .order_by(models.Classification.created_at.desc())
        .first()
    )
    if payload.category or payload.department or payload.priority or payload.reason:
        classification = models.Classification(
            tenant_id=item.tenant_id,
            document_id=item.id,
            category=payload.category or (existing_cls.category if existing_cls else "manual_review"),
            department=payload.department or (existing_cls.department if existing_cls else "triage"),
            confidence=1.0,
            priority=payload.priority or (existing_cls.priority if existing_cls else "normal"),
            reason=payload.reason or "manual_review_approved",
            source="manual",
        )
        db.add(classification)

    if payload.extraction is not None:
        db.add(models.Extraction(tenant_id=item.tenant_id, document_id=item.id, data=payload.extraction))

    item.needs_review = False
    item.status = "DONE"
    item.updated_at = datetime.utcnow()
    db.add(
        models.AuditLog(
            tenant_id=item.tenant_id,
            trace_id=item.trace_id,
            event_type="review_approved",
            entity_type="document",
            entity_id=str(item.id),
            payload={
                "category": payload.category,
                "department": payload.department,
                "priority": payload.priority,
            },
        )
    )
    db.commit()
    return {"status": "APPROVED", "document_id": str(item.id)}


@router.post("/{document_id}/reprocess")
def reprocess_review(document_id: str):
    process_document.delay(document_id)
    return {"status": "QUEUED"}
