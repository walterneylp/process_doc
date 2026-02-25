from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1 import api_router
from backend.app.core.logging import setup_logging
from backend.app.db.session import Base, engine

setup_logging()
app = FastAPI(title="Enterprise Processing Engine")
app.include_router(api_router, prefix="/api/v1")
web_dir = Path(__file__).parent / "web"
app.mount("/dashboard", StaticFiles(directory=str(web_dir), html=True), name="dashboard")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/health")
def health():
    return {"status": "ok", "service": "EPE"}
