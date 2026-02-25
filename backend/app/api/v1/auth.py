from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.db import models
from backend.app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    tenant_slug: str
    email: EmailStr
    password: str
    full_name: str


@router.post("/register")
def register(payload: RegisterPayload, db: Annotated[Session, Depends(get_db)]):
    tenant = db.query(models.Tenant).filter(models.Tenant.slug == payload.tenant_slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    user = models.User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email}


@router.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")

    role_item = (
        db.query(models.Role.name)
        .join(models.UserRole, models.UserRole.role_id == models.Role.id)
        .filter(models.UserRole.user_id == user.id)
        .first()
    )
    token = create_access_token(
        {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "role": role_item[0] if role_item else "user",
        }
    )
    return {"access_token": token, "token_type": "bearer"}
