from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import func

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.domain.billing.service import get_or_create_usage

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    emails = db.query(func.count(models.Email.id)).filter(models.Email.tenant_id == current_user.tenant_id).scalar()
    docs = db.query(func.count(models.Document.id)).filter(models.Document.tenant_id == current_user.tenant_id).scalar()
    review = (
        db.query(func.count(models.Document.id))
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.needs_review == True)
        .scalar()
    )
    return {"emails": emails, "documents": docs, "needs_review": review}


@router.get("/usage")
def usage(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = get_or_create_usage(db, current_user.tenant_id)
    return {"period": item.period, "emails_processed": item.emails_processed, "llm_calls": item.llm_calls}


@router.get("/html", response_class=HTMLResponse)
def html_dashboard(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    data = summary(db, current_user)
    return f"""
    <html><body>
      <h1>EPE Dashboard</h1>
      <ul>
        <li>Emails: {data['emails']}</li>
        <li>Documentos: {data['documents']}</li>
        <li>Revisão: {data['needs_review']}</li>
      </ul>
    </body></html>
    """
