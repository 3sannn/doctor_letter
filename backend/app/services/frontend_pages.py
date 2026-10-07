from pathlib import Path

# Clean URL path -> HTML file under frontend/
PAGE_ROUTES: dict[str, str] = {
    "/": "index.html",
    "/dashboard": "dashboard.html",
    "/templates": "templates.html",
    "/editor": "editor.html",
    "/history": "history.html",
    "/profile": "profile.html",
    "/privacy": "privacy.html",
}

# Friendly aliases (permanent redirect to canonical path)
PAGE_ALIASES: dict[str, str] = {
    "/workspace": "/dashboard",
    "/letters": "/history",
    "/sign-in": "/",
    "/login": "/",
}

HTML_EXTENSION_REDIRECTS: dict[str, str] = {
    "/index.html": "/",
    **{f"{path}.html": path for path in PAGE_ROUTES if path != "/"},
}


def resolve_frontend_file(frontend_dir: Path, clean_path: str) -> Path | None:
    filename = PAGE_ROUTES.get(clean_path)
    if not filename:
        return None
    candidate = (frontend_dir / filename).resolve()
    root = frontend_dir.resolve()
    if root not in candidate.parents and candidate != root:
        return None
    if not candidate.is_file():
        return None
    return candidate
