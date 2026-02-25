import uuid

from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.utils.crypto import encrypt_secret


def create_email_account(db: Session, tenant_id, data: dict) -> models.EmailAccount:
    account = models.EmailAccount(
        tenant_id=tenant_id,
        name=data["name"],
        imap_host=data["imap_host"],
        imap_port=data["imap_port"],
        imap_username=data["imap_username"],
        imap_password_enc=encrypt_secret(data["imap_password"]),
        use_ssl=data.get("use_ssl", True),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: Session, tenant_id):
    return db.query(models.EmailAccount).filter(models.EmailAccount.tenant_id == tenant_id).all()


def create_email_if_missing(db: Session, tenant_id, account_id, payload: dict) -> models.Email | None:
    exists = (
        db.query(models.Email)
        .filter(models.Email.tenant_id == tenant_id, models.Email.message_id == payload["message_id"])
        .first()
    )
    if exists:
        return None
    item = models.Email(
        tenant_id=tenant_id,
        email_account_id=account_id,
        message_id=payload["message_id"],
        subject=payload.get("subject"),
        sender=payload.get("sender"),
        body_text=payload.get("body_text"),
        status="RECEIVED",
        trace_id=payload.get("trace_id", uuid.uuid4().hex),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_email_attachment(
    db: Session,
    tenant_id,
    email_id,
    filename: str,
    mime_type: str | None,
    file_path: str,
    sha256: str,
) -> models.EmailAttachment:
    existing = (
        db.query(models.EmailAttachment)
        .filter(
            models.EmailAttachment.tenant_id == tenant_id,
            models.EmailAttachment.email_id == email_id,
            models.EmailAttachment.sha256 == sha256,
        )
        .first()
    )
    if existing:
        return existing

    item = models.EmailAttachment(
        tenant_id=tenant_id,
        email_id=email_id,
        filename=filename,
        file_path=file_path,
        sha256=sha256,
        mime_type=mime_type,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
