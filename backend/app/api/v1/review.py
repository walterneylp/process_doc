from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models

router = APIRouter(prefix="/review", tags=["review"])


@router.get("")
def review_queue(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = (
        db.query(models.Document)
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.needs_review == True)
        .all()
    )
    return [{"id": str(i.id), "status": i.status, "trace_id": i.trace_id} for i in items]
