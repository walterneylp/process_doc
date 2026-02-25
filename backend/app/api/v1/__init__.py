from fastapi import APIRouter

from backend.app.api.v1 import auth, configs, dashboard, documents, email_accounts, emails, review, tenants, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(users.router)
api_router.include_router(email_accounts.router)
api_router.include_router(emails.router)
api_router.include_router(documents.router)
api_router.include_router(configs.router)
api_router.include_router(dashboard.router)
api_router.include_router(review.router)
