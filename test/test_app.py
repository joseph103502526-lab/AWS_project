import os
import sys

import pytest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_status_code(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_returns_feature4_ui(client):
    response = client.get("/")
    assert b"CPU Stress Monitor" in response.data
    assert b"/feature4" in response.data


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_not_found(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_feature1(client):
    response = client.get("/feature1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["message"] == "Feature 1 completed"


def test_feature2(client):
    response = client.get("/feature2")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["message"] == "Feature 2 completed"


def test_feature4_short_duration(client):
    response = client.get("/feature4?duration=1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["duration_seconds"] == 1
    assert data["workers"] >= 1
