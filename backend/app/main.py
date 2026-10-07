from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.database import Base, engine
from app.database_migrate import run_migrations
from app.middleware.pretty_urls import PrettyUrlMiddleware
from app.routes import drafts, health, letters, profile, session, templates, workspace
from app.routes.pages import register_frontend_pages
from app.startup import validate_settings


class StaticCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        settings = get_settings()
        max_age = settings.static_cache_seconds
        if path.startswith("/css/") or path.startswith("/js/") or path.startswith("/vendor/"):
            response.headers["Cache-Control"] = f"public, max-age={max_age}, immutable"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if get_settings().is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_settings(settings)
    Base.metadata.create_all(bind=engine)
    run_migrations()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url = None if settings.is_production else "/docs"
    redoc_url = None if settings.is_production else "/redoc"

    app = FastAPI(title="Doctor Letter", lifespan=lifespan, docs_url=docs_url, redoc_url=redoc_url)

    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(StaticCacheMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(PrettyUrlMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(session.router)
    app.include_router(workspace.router)
    app.include_router(profile.router)
    app.include_router(templates.router)
    app.include_router(drafts.router)
    app.include_router(letters.router)

    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if frontend_dir.is_dir():
        register_frontend_pages(app, frontend_dir)
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


app = create_app()
