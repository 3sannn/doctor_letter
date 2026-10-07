from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from starlette.requests import Request

from app.services.frontend_pages import PAGE_ALIASES, PAGE_ROUTES


def register_frontend_pages(app, frontend_dir: Path) -> None:
    for clean_path, filename in PAGE_ROUTES.items():
        file_path = frontend_dir / filename

        async def serve_page(_request: Request, resolved: Path = file_path) -> FileResponse:
            if not resolved.is_file():
                raise HTTPException(status_code=404)
            return FileResponse(resolved, media_type="text/html")

        app.add_api_route(
            clean_path,
            serve_page,
            methods=["GET"],
            include_in_schema=False,
            name=f"page_{filename.replace('.', '_')}",
        )

    for alias_path, target_path in PAGE_ALIASES.items():

        async def redirect_alias(_request: Request, target: str = target_path) -> RedirectResponse:
            return RedirectResponse(url=target, status_code=301)

        app.add_api_route(
            alias_path,
            redirect_alias,
            methods=["GET"],
            include_in_schema=False,
            name=f"alias_{alias_path.strip('/').replace('/', '_') or 'root'}",
        )
