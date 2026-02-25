from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.adapters.email.imap_client import ImapClientAdapter
from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.domain.email.service import create_email_account, list_accounts
from backend.app.workers.tasks import sync_email_account

router = APIRouter(prefix="/email-accounts", tags=["email_accounts"])


class AccountPayload(BaseModel):
    name: str
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    use_ssl: bool = True


@router.post("")
def create_account(payload: AccountPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    item = create_email_account(db, current_user.tenant_id, payload.model_dump())
    return {"id": str(item.id), "name": item.name}


@router.get("")
def get_accounts(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    return [
        {"id": str(a.id), "name": a.name, "imap_host": a.imap_host, "imap_username": a.imap_username}
        for a in list_accounts(db, current_user.tenant_id)
    ]


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
