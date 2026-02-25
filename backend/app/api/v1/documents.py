from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.workers.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = db.query(models.Document).filter(models.Document.tenant_id == current_user.tenant_id).all()
    return [
        {
            "id": str(i.id),
            "doc_type": i.doc_type,
            "status": i.status,
            "needs_review": i.needs_review,
            "trace_id": i.trace_id,
        }
        for i in items
    ]


@router.get("/review")
def list_review(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = (
        db.query(models.Document)
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.needs_review == True)
        .all()
    )
    return [{"id": str(i.id), "status": i.status} for i in items]


@router.post("/{document_id}/process")
def run_document(document_id: str):
    process_document.delay(document_id)
    return {"status": "QUEUED"}
