import os
os.environ["DATABASE_URL"] = "sqlite:///./test_cases.db"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-bytes-long-for-hs256"

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
import models  # noqa: F401


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    token = pyjwt.encode(
        {"sub": "1", "email": "officer@police.gov.in", "role": "INVESTIGATING_OFFICER",
         "org": "Delhi Police", "type": "access", "iat": now, "exp": now + timedelta(minutes=30)},
        os.environ["JWT_SECRET"], algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_case(client, auth_headers):
    resp = client.post("/cases", json={"case_number": "CASE-1001", "title": "Theft investigation"},
                        headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["case_number"] == "CASE-1001"
    assert body["status"] == "OPEN"
    assert body["priority"] == "MEDIUM"
    assert body["created_by"] == "officer@police.gov.in"
    assert body["organization"] == "Delhi Police"


def test_duplicate_case_number_rejected(client, auth_headers):
    client.post("/cases", json={"case_number": "CASE-1002", "title": "First"}, headers=auth_headers)
    resp = client.post("/cases", json={"case_number": "CASE-1002", "title": "Duplicate"}, headers=auth_headers)
    assert resp.status_code == 409


def test_list_cases(client, auth_headers):
    client.post("/cases", json={"case_number": "CASE-A", "title": "A"}, headers=auth_headers)
    client.post("/cases", json={"case_number": "CASE-B", "title": "B"}, headers=auth_headers)
    resp = client.get("/cases", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_case_by_number(client, auth_headers):
    client.post("/cases", json={"case_number": "CASE-XYZ", "title": "Findable"}, headers=auth_headers)
    resp = client.get("/cases/CASE-XYZ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Findable"


def test_get_nonexistent_case_404s(client, auth_headers):
    resp = client.get("/cases/DOES-NOT-EXIST", headers=auth_headers)
    assert resp.status_code == 404


def test_update_case_status(client, auth_headers):
    client.post("/cases", json={"case_number": "CASE-STATUS", "title": "T"}, headers=auth_headers)
    resp = client.patch("/cases/CASE-STATUS/status", json={"status": "CLOSED"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"


def test_unauthenticated_request_rejected(client):
    resp = client.get("/cases")
    assert resp.status_code in (401, 403)  # FastAPI's HTTPBearer returns 403 when the header is missing entirely


# --- the stats endpoint, since it's what drives the dashboard cards ------

def test_stats_reflect_real_data_not_hardcoded(client, auth_headers):
    client.post("/cases", json={"case_number": "S-1", "title": "a", "priority": "HIGH"}, headers=auth_headers)
    client.post("/cases", json={"case_number": "S-2", "title": "b", "priority": "LOW"}, headers=auth_headers)
    client.post("/cases", json={"case_number": "S-3", "title": "c", "priority": "HIGH"}, headers=auth_headers)
    client.patch("/cases/S-3/status", json={"status": "PENDING_REVIEW"}, headers=auth_headers)

    stats = client.get("/cases/stats", headers=auth_headers).json()
    assert stats["total_cases"] == 3
    assert stats["pending_review"] == 1
    # S-1 is HIGH+OPEN (counts), S-3 is HIGH+PENDING_REVIEW (still counts, not CLOSED)
    assert stats["high_priority"] == 2
    assert stats["active_cases"] == 2  # S-1 (OPEN) and S-2 (OPEN); S-3 moved to PENDING_REVIEW


def test_stats_on_empty_db_are_genuinely_zero(client, auth_headers):
    stats = client.get("/cases/stats", headers=auth_headers).json()
    assert stats == {"total_cases": 0, "active_cases": 0, "pending_review": 0, "high_priority": 0}
