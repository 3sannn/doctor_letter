def test_clean_page_routes(client):
    for path in ("/", "/dashboard", "/templates", "/editor", "/history", "/profile", "/privacy"):
        response = client.get(path)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


def test_html_extension_redirects(client):
    response = client.get("/dashboard.html", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].endswith("/dashboard")

    response = client.get("/index.html", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].rstrip("/").endswith("")


def test_url_aliases(client):
    response = client.get("/workspace", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].endswith("/dashboard")

    response = client.get("/letters", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].endswith("/history")


def test_editor_html_redirect_preserves_query(client):
    response = client.get("/editor.html?template=blank-letter", follow_redirects=False)
    assert response.status_code == 301
    location = response.headers["location"]
    assert "/editor" in location
    assert "template=blank-letter" in location
