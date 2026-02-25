from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.workers.tasks import process_email

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
def list_emails(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = db.query(models.Email).filter(models.Email.tenant_id == current_user.tenant_id).all()
    return [
        {
            "id": str(i.id),
            "subject": i.subject,
            "sender": i.sender,
            "status": i.status,
            "trace_id": i.trace_id,
        }
        for i in items
    ]


@router.post("/{email_id}/process")
def run_email(email_id: str):
    process_email.delay(email_id)
    return {"status": "QUEUED"}
