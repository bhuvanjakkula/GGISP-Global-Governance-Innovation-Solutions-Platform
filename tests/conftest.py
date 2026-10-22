import os
import pytest
from fastapi.testclient import TestClient

from ggisp.main import app
from ggisp.db import init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = str(tmp_path / "test_ggisp.db")
    monkeypatch.setenv("GGISP_DB_PATH", test_db_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    with TestClient(app) as test_client:
        yield test_client


def make_project(client):
    response = client.post('/api/projects', json={
        'domain_slug': 'sovereign-debt', 'title': 'Debt and development test',
        'problem': 'What happens to illustrative debt paths with different interest rate assumptions?'
    })
    assert response.status_code == 201, response.text
    return response.json()['id']

