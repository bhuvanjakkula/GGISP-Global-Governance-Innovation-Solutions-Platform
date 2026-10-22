"""Tests for Authentication, User Registration, and Author Sovereign Access."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ggisp.auth import (
    AUTHOR_EMAIL,
    generate_session_token,
    get_user_by_email,
    hash_password,
    init_auth_tables,
    verify_password,
    verify_session_token,
)
from ggisp.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_auth_tables():
    init_auth_tables()
    from ggisp.db import db
    with db() as con:
        con.execute("DELETE FROM users WHERE lower(email) != lower(?)", (AUTHOR_EMAIL,))



def test_password_hashing_and_verification():
    pw = "SuperSecure123!"
    h, salt = hash_password(pw)
    assert len(h) == 64  # SHA-256 hex length
    assert len(salt) == 32  # 16 bytes in hex
    assert verify_password(pw, h, salt) is True
    assert verify_password("WrongPassword!", h, salt) is False


def test_session_token_generation_and_verification():
    token = generate_session_token(42, "researcher@example.org", "researcher")
    claims = verify_session_token(token)
    assert claims is not None
    assert claims["uid"] == 42
    assert claims["email"] == "researcher@example.org"
    assert claims["is_author"] is False

    # Author token
    auth_token = generate_session_token(1, AUTHOR_EMAIL, "author")
    auth_claims = verify_session_token(auth_token)
    assert auth_claims is not None
    assert auth_claims["is_author"] is True


def test_author_seeded_in_database():
    author = get_user_by_email(AUTHOR_EMAIL)
    assert author is not None
    assert author["role"] == "author"
    assert author["tier"] == "author_all_access"


def test_signup_regular_user():
    email = "un_analyst_2026@domain.org"
    res = client.post("/api/auth/signup", json={
        "full_name": "Dr. Sarah Chen",
        "email": email,
        "mobile_number": "+1 415 555 2671",
        "password": "StrongPassword2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == email
    assert data["user"]["mobile_number"] == "+1 415 555 2671"
    assert data["user"]["is_author"] is False
    assert "token" in data


def test_author_signup_and_elevation():
    res = client.post("/api/auth/signup", json={
        "full_name": "Bhuvan Jakkula",
        "email": AUTHOR_EMAIL,
        "mobile_number": "+91 9876543210",
        "password": "AuthorPasswordSecure"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"].lower() == AUTHOR_EMAIL.lower()
    assert data["user"]["is_author"] is True
    assert data["user"]["role"] == "author"
    assert data["user"]["access_all_features"] is True


def test_author_signin_seamless():
    # Author signs in seamlessly
    res = client.post("/api/auth/signin", json={
        "email": AUTHOR_EMAIL,
        "password": ""
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["is_author"] is True
    assert data["user"]["role"] == "author"
    assert "token" in data


def test_regular_user_signin_success_and_failure():
    email = "economist_geneva@wto.org"
    client.post("/api/auth/signup", json={
        "full_name": "Marc Dupuis",
        "email": email,
        "mobile_number": "+41 22 739 5111",
        "password": "WTOSecretPassword123"
    })

    # Wrong password fails
    fail_res = client.post("/api/auth/signin", json={
        "email": email,
        "password": "IncorrectPassword"
    })
    assert fail_res.status_code == 401

    # Correct password succeeds
    ok_res = client.post("/api/auth/signin", json={
        "email": email,
        "password": "WTOSecretPassword123"
    })
    assert ok_res.status_code == 200
    assert ok_res.json()["user"]["email"] == email


def test_direct_author_access_endpoint():
    res = client.post("/api/auth/author-access", json={
        "email": AUTHOR_EMAIL
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["is_author"] is True

    # Unauthorized email rejected
    rej = client.post("/api/auth/author-access", json={
        "email": "impostor@unknown.com"
    })
    assert rej.status_code == 403


def test_get_me_profile_with_permissions():
    # 1. Author profile
    auth_res = client.post("/api/auth/author-access", json={"email": AUTHOR_EMAIL})
    token = auth_res.json()["token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["authenticated"] is True
    assert me["is_author"] is True
    assert "ALL_13_DIVISIONS" in me["permissions"]
    assert "FOUNDER_POLICY_APPROVAL" in me["permissions"]

    # 2. Unauthenticated request
    guest_res = client.get("/api/auth/me")
    assert guest_res.status_code == 200
    assert guest_res.json()["authenticated"] is False
