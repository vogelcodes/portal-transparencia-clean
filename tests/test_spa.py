import importlib
import os
import sys
from pathlib import Path

import pytest
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import JSON

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def app_client():
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["APP_ENV"] = "test"

    pg.JSONB = JSON

    app_module = importlib.import_module("src.app")
    app_module = importlib.reload(app_module)

    app = app_module.app
    db = app_module.db
    User = app_module.User

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(
            username="spa_user",
            email="spa@example.com",
            password_hash="hash",
            salt="salt",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True

    yield client



def test_spa_route_renders_shell(app_client):
    response = app_client.get("/SPA")

    assert response.status_code == 200
    assert b"id=\"spa-app\"" in response.data
    assert b"Portal Transparencia SPA" in response.data



def test_spa_dashboard_endpoint_returns_structured_data(app_client):
    response = app_client.get("/api/spa/dashboard")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "uasgs" in payload
    assert "searches" in payload
    assert "cache" in payload



def test_spa_dashboard_endpoint_marks_cache_on_second_request(app_client):
    first = app_client.get("/api/spa/dashboard").get_json()
    second = app_client.get("/api/spa/dashboard").get_json()

    assert first["cache"]["cached"] is False
    assert second["cache"]["cached"] is True
