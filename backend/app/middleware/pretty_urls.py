from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.config import get_settings
from app.services.frontend_pages import HTML_EXTENSION_REDIRECTS, PAGE_ALIASES, PAGE_ROUTES


class PrettyUrlMiddleware(BaseHTTPMiddleware):
    """Normalize public URLs: drop .html, trim trailing slashes, optional production-only rules."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in ("GET", "HEAD"):
            return await call_next(request)

        path = request.url.path
        if path.startswith("/api/") or path.startswith("/css/") or path.startswith("/js/") or path.startswith("/vendor/"):
            return await call_next(request)

        settings = get_settings()

        if path in HTML_EXTENSION_REDIRECTS:
            target = HTML_EXTENSION_REDIRECTS[path]
            return RedirectResponse(url=str(request.url.replace(path=target)), status_code=301)

        if path != "/" and path.endswith("/"):
            trimmed = path.rstrip("/") or "/"
            if trimmed in PAGE_ROUTES or trimmed in PAGE_ALIASES:
                return RedirectResponse(url=str(request.url.replace(path=trimmed)), status_code=301)

        if settings.is_production and path == "/index":
            return RedirectResponse(url=str(request.url.replace(path="/")), status_code=301)

        return await call_next(request)
