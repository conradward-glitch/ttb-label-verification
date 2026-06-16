from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_without_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "key_loaded": False, "key_prefix": "none"}


def test_health_endpoint_reports_anthropic_key_prefix(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123456")

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "key_loaded": True, "key_prefix": "sk-ant-t"}


def test_verify_rejects_non_image_upload():
    response = client.post(
        "/api/verify",
        data={"application_data": '{"brand_name":"OLD TOM DISTILLERY"}'},
        files={"label_image": ("label.txt", b"not image", "text/plain")},
    )
    assert response.status_code == 400
    assert "PNG or JPG" in response.json()["detail"]
