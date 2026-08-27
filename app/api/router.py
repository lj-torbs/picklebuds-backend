from fastapi import APIRouter

from app.api.routes import admin, auth, bookings, owners, pasalo, venues


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(venues.router, prefix="/venues", tags=["venues"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(pasalo.router, prefix="/pasalo", tags=["pasalo"])
api_router.include_router(owners.router, prefix="/owners", tags=["owners"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
