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
    done_docs = (
        db.query(func.count(models.Document.id))
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.status == "DONE")
        .scalar()
    )
    review = (
        db.query(func.count(models.Document.id))
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.needs_review == True)
        .scalar()
    )
    review_rate = round((review / docs) * 100, 2) if docs else 0.0
    approval_rate = round(((docs - review) / docs) * 100, 2) if docs else 0.0
    return {
        "emails": emails,
        "documents": docs,
        "done_documents": done_docs,
        "needs_review": review,
        "review_rate": review_rate,
        "approval_rate": approval_rate,
    }


@router.get("/usage")
def usage(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = get_or_create_usage(db, current_user.tenant_id)
    docs = db.query(func.count(models.Document.id)).filter(models.Document.tenant_id == current_user.tenant_id).scalar()
    done_docs = (
        db.query(func.count(models.Document.id))
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.status == "DONE")
        .scalar()
    )
    manual_reviews = (
        db.query(func.count(models.Classification.id))
        .filter(models.Classification.tenant_id == current_user.tenant_id, models.Classification.source == "manual")
        .scalar()
    )
    avg_processing_seconds = (
        db.query(
            func.avg(
                func.extract(
                    "epoch",
                    models.Document.updated_at - models.Document.created_at,
                )
            )
        )
        .filter(
            models.Document.tenant_id == current_user.tenant_id,
            models.Document.status == "DONE",
            models.Document.updated_at.isnot(None),
        )
        .scalar()
    )
    success_rate = round((done_docs / docs) * 100, 2) if docs else 0.0
    return {
        "period": item.period,
        "emails_processed": item.emails_processed,
        "llm_calls": item.llm_calls,
        "manual_reviews": manual_reviews,
        "success_rate": success_rate,
        "avg_processing_seconds": round(float(avg_processing_seconds), 2) if avg_processing_seconds else 0.0,
    }


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
