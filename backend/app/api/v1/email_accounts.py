from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.adapters.email.imap_client import ImapClientAdapter
from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.domain.email.service import create_email_account, get_account_sync_interval, list_accounts, set_account_sync_interval
from backend.app.workers.tasks import sync_email_account

router = APIRouter(prefix="/email-accounts", tags=["email_accounts"])


class AccountPayload(BaseModel):
    name: str
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    use_ssl: bool = True
    sync_interval_minutes: int = 5


class AccountUpdatePayload(BaseModel):
    name: str | None = None
    imap_host: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    imap_password: str | None = None
    use_ssl: bool | None = None
    sync_interval_minutes: int | None = None
    is_active: bool | None = None


ALLOWED_SYNC_INTERVALS = {5, 15, 30, 60, 240, 720}


@router.post("")
def create_account(payload: AccountPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    if payload.sync_interval_minutes not in ALLOWED_SYNC_INTERVALS:
        raise HTTPException(status_code=400, detail="invalid_sync_interval")
    item = create_email_account(db, current_user.tenant_id, payload.model_dump())
    return {"id": str(item.id), "name": item.name, "sync_interval_minutes": payload.sync_interval_minutes}


@router.get("")
def get_accounts(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "imap_host": a.imap_host,
            "imap_port": a.imap_port,
            "imap_username": a.imap_username,
            "use_ssl": a.use_ssl,
            "is_active": a.is_active,
            "sync_interval_minutes": get_account_sync_interval(db, current_user.tenant_id, a.id, 5),
        }
        for a in list_accounts(db, current_user.tenant_id)
    ]


@router.put("/{account_id}")
def update_account(
    account_id: str,
    payload: AccountUpdatePayload,
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
):
    account = (
        db.query(models.EmailAccount)
        .filter(models.EmailAccount.id == account_id, models.EmailAccount.tenant_id == current_user.tenant_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="account_not_found")

    data = payload.model_dump(exclude_unset=True)
    if "sync_interval_minutes" in data:
        interval = int(data["sync_interval_minutes"])
        if interval not in ALLOWED_SYNC_INTERVALS:
            raise HTTPException(status_code=400, detail="invalid_sync_interval")
        set_account_sync_interval(db, current_user.tenant_id, account.id, interval)

    if "name" in data:
        account.name = data["name"]
    if "imap_host" in data:
        account.imap_host = data["imap_host"]
    if "imap_port" in data:
        account.imap_port = data["imap_port"]
    if "imap_username" in data:
        account.imap_username = data["imap_username"]
    if "imap_password" in data:
        from backend.app.utils.crypto import encrypt_secret

        account.imap_password_enc = encrypt_secret(data["imap_password"])
    if "use_ssl" in data:
        account.use_ssl = data["use_ssl"]
    if "is_active" in data:
        account.is_active = data["is_active"]
    db.commit()
    return {"status": "UPDATED", "id": str(account.id)}


@router.post("/{account_id}/test")
def test_account(account_id: str, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    account = (
        db.query(models.EmailAccount)
        .filter(models.EmailAccount.id == account_id, models.EmailAccount.tenant_id == current_user.tenant_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="account_not_found")

    client = ImapClientAdapter(
        host=account.imap_host,
        port=account.imap_port,
        username=account.imap_username,
        password_enc=account.imap_password_enc,
        use_ssl=account.use_ssl,
    )
    return {"ok": client.test_connection()}


@router.post("/{account_id}/sync")
def sync_account(account_id: str, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    account = (
        db.query(models.EmailAccount)
        .filter(models.EmailAccount.id == account_id, models.EmailAccount.tenant_id == current_user.tenant_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="account_not_found")
    sync_email_account.delay(str(account.id))
    return {"status": "QUEUED"}
