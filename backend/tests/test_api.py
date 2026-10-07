import pytest

from app.schemas import SessionCreate


def test_mobile_normalization():
    payload = SessionCreate(mobile=" 98765 43210 ")
    assert payload.mobile == "9876543210"


def test_mobile_rejects_invalid_indian_start():
    with pytest.raises(ValueError):
        SessionCreate(mobile="5123456789")


def test_session_rejects_honeypot():
    with pytest.raises(ValueError):
        SessionCreate(mobile="9123456789", company="spam")


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_session_and_profile(auth_client):
    profile = auth_client.get("/api/profile")
    assert profile.status_code == 200
    assert profile.json()["mobile"] == "9123456789"

    updated = auth_client.put(
        "/api/profile",
        json={
            "full_name": "Dr Test User",
            "registration_number": "REG-001",
            "clinic_name": "Test Clinic",
            "clinic_address": "Test City",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Dr Test User"


def test_templates_list(client):
    response = client.get("/api/templates")
    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()}
    assert "referral-letter" in slugs
    assert "blank-letter" in slugs
    assert "medical-certificate" in slugs


def test_template_requires_auth(client):
    response = client.get("/api/templates/referral-letter")
    assert response.status_code == 401


def test_draft_save_and_load(auth_client):
    auth_client.put(
        "/api/drafts",
        json={
            "template_slug": "referral-letter",
            "html_content": "<p>Patient Name: Sample</p>" * 3,
            "patient_name": "Sample",
        },
    )
    draft = auth_client.get("/api/drafts/by-template/referral-letter")
    assert draft.status_code == 200
    assert draft.json()["patient_name"] == "Sample"


def test_preview_pdf(auth_client):
    template = auth_client.get("/api/templates/referral-letter")
    html = template.json()["html"]
    preview = auth_client.post(
        "/api/letters/preview",
        json={"template_slug": "referral-letter", "html_content": html},
    )
    assert preview.status_code == 200
    assert preview.json()["pdf_base64"]


def test_workspace_bundle(auth_client):
    response = auth_client.get("/api/workspace")
    assert response.status_code == 200
    body = response.json()
    assert "profile" in body
    assert "drafts" in body
    assert body["profile"]["mobile"] == "9123456789"


def test_editor_setup(auth_client):
    response = auth_client.get("/api/editor/referral-letter")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "referral-letter"
    assert body["html"]


def test_finalize_requires_s3(auth_client):
    from app.config import get_settings

    settings = get_settings()
    if not settings.aws_s3_bucket.strip():
        pytest.skip("AWS_S3_BUCKET not configured")
    if not settings.aws_access_key_id.strip() or not settings.aws_secret_access_key.strip():
        pytest.skip("AWS credentials not configured")

    template = auth_client.get("/api/templates/referral-letter")
    html = template.json()["html"]
    response = auth_client.post(
        "/api/letters/finalize",
        json={
            "template_slug": "referral-letter",
            "html_content": html,
            "patient_name": "Sample Patient",
        },
    )
    if response.status_code == 503:
        pytest.skip("S3 storage unavailable in this environment")
    assert response.status_code == 201
    letter_id = response.json()["id"]

    download = auth_client.get(f"/api/letters/{letter_id}/download")
    assert download.status_code == 200
    assert download.json()["url"]

    deleted = auth_client.delete(f"/api/letters/{letter_id}")
    assert deleted.status_code == 200
