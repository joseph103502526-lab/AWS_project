import sys
import os

# 確保 pytest 可以找到 src/ 模組
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from app import app


@pytest.fixture
def client():
    """建立 Flask 測試用戶端。"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_status_code(client):
    """測試首頁回傳 HTTP 200。"""
    response = client.get("/")
    assert response.status_code == 200


def test_index_returns_html(client):
    """測試首頁回傳 HTML 內容。"""
    response = client.get("/")
    assert b"Feature" in response.data


def test_health_check(client):
    """測試 /health 端點回傳 200 且狀態為 healthy。"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_not_found(client):
    """測試不存在的路由回傳 404。"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_feature1(client):
    """測試 /feature1 回傳正確訊息「早上要看股票」。"""
    response = client.get("/feature1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["message"] == "早上要看股票"


def test_feature2(client):
    """測試 /feature2 回傳正確訊息「要找下午上班的公司」。"""
    response = client.get("/feature2")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["message"] == "要找下午上班的公司"
