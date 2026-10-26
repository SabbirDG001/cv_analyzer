from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, me, reference
from app.core.auth import get_current_user
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="SkillBridge API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    # Every other router requires a verified Supabase JWT.
    protected = [Depends(get_current_user)]
    app.include_router(reference.router, dependencies=protected)
    app.include_router(me.router, dependencies=protected)
    return app


app = create_app()
