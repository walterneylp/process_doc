from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.db import models


def seed_plans(db: Session) -> None:
    defaults = [
        ("Starter", 1000, 300),
        ("Pro", 10000, 5000),
        ("Business", None, None),
    ]
    for name, email_limit, llm_limit in defaults:
        exists = db.query(models.Plan).filter(models.Plan.name == name).first()
        if not exists:
            db.add(
                models.Plan(
                    name=name,
                    monthly_email_limit=email_limit,
                    monthly_llm_calls_limit=llm_limit,
                )
            )
    db.commit()


def get_or_create_usage(db: Session, tenant_id) -> models.TenantUsage:
    period = datetime.utcnow().strftime("%Y-%m")
    usage = (
        db.query(models.TenantUsage)
        .filter(models.TenantUsage.tenant_id == tenant_id, models.TenantUsage.period == period)
        .first()
    )
    if usage:
        return usage
    usage = models.TenantUsage(tenant_id=tenant_id, period=period, emails_processed=0, llm_calls=0)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage
