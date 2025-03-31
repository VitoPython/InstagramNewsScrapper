from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

def test_read_main():
    """Test that the main route returns HTTP 200"""
    response = client.get("/")
    assert response.status_code == 200

def test_api_docs():
    """Test that the API docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_get_available_sources():
    """Test that the news sources endpoint returns a list"""
    response = client.get("/news/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0 