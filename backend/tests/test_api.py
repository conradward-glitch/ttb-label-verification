from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_verify_rejects_non_image_upload():
    response = client.post(
        "/api/verify",
        data={"application_data": '{"brand_name":"OLD TOM DISTILLERY"}'},
        files={"label_image": ("label.txt", b"not image", "text/plain")},
    )
    assert response.status_code == 400
    assert "PNG or JPG" in response.json()["detail"]
