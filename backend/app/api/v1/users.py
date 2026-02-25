from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.api.v1.deps import DbDep, get_current_user, require_role
from backend.app.core.security import hash_password
from backend.app.db import models

router = APIRouter(prefix="/users", tags=["users"])


class UserPayload(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "user"


@router.post("")
def create_user(payload: UserPayload, db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    require_role(db, current_user, "admin")
    user = models.User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    role = db.query(models.Role).filter(models.Role.name == payload.role).first()
    if not role:
        role = models.Role(name=payload.role)
        db.add(role)
        db.flush()
    db.add(models.UserRole(tenant_id=current_user.tenant_id, user_id=user.id, role_id=role.id))

    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email}


@router.get("")
def list_users(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = db.query(models.User).filter(models.User.tenant_id == current_user.tenant_id).all()
    return [{"id": str(u.id), "email": u.email, "full_name": u.full_name} for u in items]
