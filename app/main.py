from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.owner_branding import OwnerBrandingSettings
from app.models.system_fee import OwnerSystemFeeSetting


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def ensure_addon_tables() -> None:
    OwnerBrandingSettings.__table__.create(bind=engine, checkfirst=True)
    OwnerSystemFeeSetting.__table__.create(bind=engine, checkfirst=True)
