from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.utils.file_types import infer_doc_type


def create_document_from_attachment(db: Session, tenant_id, email_id, attachment_id, filename: str, trace_id: str):
    doc = models.Document(
        tenant_id=tenant_id,
        email_id=email_id,
        attachment_id=attachment_id,
        doc_type=infer_doc_type(filename),
        trace_id=trace_id,
        status="QUEUED",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents(db: Session, tenant_id):
    return db.query(models.Document).filter(models.Document.tenant_id == tenant_id).all()
