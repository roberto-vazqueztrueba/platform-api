from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root() -> None:
  response = client.get("/")
  assert response.status_code == 200
  assert response.json()["message"] == "hello platform"

def test_health_endpoints() -> None:
  assert client.get("/health/live").json() == {"status": "alive"}
  assert client.get("/health/ready").json() == {"status": "ready"}
