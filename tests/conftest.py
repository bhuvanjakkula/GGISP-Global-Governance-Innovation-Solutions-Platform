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
