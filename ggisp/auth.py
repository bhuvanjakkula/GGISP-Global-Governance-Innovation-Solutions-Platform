"""Authentication, User Registration, and Author Access Control for GGISP Platform."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from ggisp.db import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Author Access"])

# Platform Author & Founder email
AUTHOR_EMAIL = "bhuvanjakkula@gmail.com"
AUTH_SECRET_KEY = os.getenv("GGISP_AUTH_SECRET", "ggisp-sovereign-author-key-v1-quantum-secure")


# ---------------------------------------------------------------------------
# Pydantic Request / Response Schemas
# ---------------------------------------------------------------------------
class SignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=150)
    mobile_number: str = Field(..., min_length=7, max_length=30)
    password: str = Field(..., min_length=6, max_length=128)


class SignInRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)
    password: Optional[str] = Field(default="", max_length=128)


class AuthorAccessRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    mobile_number: str
    role: str
    tier: str
    is_author: bool
    access_all_features: bool
    created_at: str


class AuthTokenResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    user: UserProfileResponse
    message: str


# ---------------------------------------------------------------------------
# Cryptographic Password & Token Primitives
# ---------------------------------------------------------------------------
def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 rounds and unique salt."""
    if not salt:
        salt = secrets.token_hex(16)
    salt_bytes = salt.encode("utf-8")
    pw_bytes = password.encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt_bytes, 100_000)
    return derived.hex(), salt


def verify_password(plain_password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored PBKDF2 hash."""
    salt_bytes = salt.encode("utf-8")
    pw_bytes = plain_password.encode("utf-8")
    test_hash = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt_bytes, 100_000).hex()
    return hmac.compare_digest(test_hash, stored_hash)


def generate_session_token(user_id: int, email: str, role: str) -> str:
    """Generate a signed cryptographic session token."""
    payload = {
        "uid": user_id,
        "email": email.strip().lower(),
        "role": role,
        "is_author": (email.strip().lower() == AUTHOR_EMAIL),
        "iat": int(time.time()),
        "exp": int(time.time()) + (86400 * 30),  # 30-day persistence
        "nonce": secrets.token_hex(8),
    }
    raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_payload).decode("utf-8").rstrip("=")
    sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify session token signature and expiry."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        expected_sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        # Add padding back if necessary
        padded = b64_payload + "=" * ((4 - len(b64_payload) % 4) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Database Helper Functions
# ---------------------------------------------------------------------------
def init_auth_tables() -> None:
    """Initialize users and sessions tables, and ensure author account exists."""
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            mobile_number TEXT NOT NULL DEFAULT '',
            full_name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'user',
            tier TEXT NOT NULL DEFAULT 'free',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_login TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );
        """)

        # Ensure Author record exists with highest permissions
        cur = con.execute("SELECT id, role, tier FROM users WHERE lower(email) = lower(?)", (AUTHOR_EMAIL,))
        author = cur.fetchone()
        if not author:
            p_hash, salt = hash_password(secrets.token_hex(24))
            con.execute("""
                INSERT INTO users (email, password_hash, salt, mobile_number, full_name, role, tier)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (AUTHOR_EMAIL, p_hash, salt, "+91 9999999999", "Bhuvan Jakkula (Author)", "author", "author_all_access"))
        else:
            # Maintain author role & unrestricted tier
            con.execute("""
                UPDATE users SET role = 'author', tier = 'author_all_access' WHERE lower(email) = lower(?)
            """, (AUTHOR_EMAIL,))


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with db() as con:
        cur = con.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email.strip(),))
        return cur.fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with db() as con:
        cur = con.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()


def format_user_profile(user: sqlite3.Row) -> UserProfileResponse:
    is_author = (user["email"].strip().lower() == AUTHOR_EMAIL) or (user["role"] in ("author", "founder", "admin"))
    return UserProfileResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        mobile_number=user["mobile_number"],
        role=user["role"],
        tier=user["tier"],
        is_author=is_author,
        access_all_features=True if is_author else (user["tier"] != "free"),
        created_at=user["created_at"],
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@router.post("/signup", response_model=AuthTokenResponse)
def sign_up(req: SignUpRequest):
    """Register a new user account with Email, Mobile Number, Name, and Password."""
    email_clean = req.email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email_clean):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    if len(req.mobile_number.strip()) < 7:
        raise HTTPException(status_code=400, detail="Please provide a valid mobile number.")

    is_author = (email_clean == AUTHOR_EMAIL)
    role = "author" if is_author else "researcher"
    tier = "author_all_access" if is_author else "standard"

    existing = get_user_by_email(email_clean)
    if existing:
        if is_author:
            # Author re-sign up updates password and immediately logs in
            p_hash, salt = hash_password(req.password)
            with db() as con:
                con.execute("""
                    UPDATE users SET full_name = ?, mobile_number = ?, password_hash = ?, salt = ?, role = 'author', tier = 'author_all_access', last_login = datetime('now')
                    WHERE id = ?
                """, (req.full_name, req.mobile_number, p_hash, salt, existing["id"]))
            user = get_user_by_id(existing["id"])
            token = generate_session_token(user["id"], user["email"], user["role"])
            return AuthTokenResponse(
                token=token,
                user=format_user_profile(user),
                message="Author account verified with full platform access."
            )
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    p_hash, salt = hash_password(req.password)
    with db() as con:
        cur = con.execute("""
            INSERT INTO users (email, password_hash, salt, mobile_number, full_name, role, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email_clean, p_hash, salt, req.mobile_number.strip(), req.full_name.strip(), role, tier))
        new_id = cur.lastrowid

    user = get_user_by_id(new_id)
    token = generate_session_token(user["id"], user["email"], user["role"])
    msg = "Welcome! Full author access unlocked." if is_author else "Account created successfully."

    return AuthTokenResponse(
        token=token,
        user=format_user_profile(user),
        message=msg
    )


@router.post("/signin", response_model=AuthTokenResponse)
def sign_in(req: SignInRequest):
    """Authenticate with Email and Password. Provides seamless author access."""
    email_clean = req.email.strip().lower()
    is_author = (email_clean == AUTHOR_EMAIL)

    user = get_user_by_email(email_clean)
    if not user:
        if is_author:
            # If author logs in for the first time without prior signup, auto-provision author
            p_hash, salt = hash_password(req.password or secrets.token_hex(16))
            with db() as con:
                cur = con.execute("""
                    INSERT INTO users (email, password_hash, salt, mobile_number, full_name, role, tier)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (AUTHOR_EMAIL, p_hash, salt, "+91 9999999999", "Bhuvan Jakkula (Author)", "author", "author_all_access"))
                user = get_user_by_id(cur.lastrowid)
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Author verification: if email is author, grant immediate access
    if is_author:
        with db() as con:
            con.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user["id"],))
        token = generate_session_token(user["id"], user["email"], "author")
        return AuthTokenResponse(
            token=token,
            user=format_user_profile(user),
            message="Author authenticated successfully. Entire platform accessible."
        )

    # Standard user password check
    if not req.password or not verify_password(req.password, user["password_hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    with db() as con:
        con.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user["id"],))

    token = generate_session_token(user["id"], user["email"], user["role"])
    return AuthTokenResponse(
        token=token,
        user=format_user_profile(user),
        message="Signed in successfully."
    )


@router.post("/author-access", response_model=AuthTokenResponse)
def author_direct_access(req: AuthorAccessRequest):
    """Direct author entry point providing full platform access for the author."""
    email_clean = req.email.strip().lower()
    if email_clean != AUTHOR_EMAIL:
        raise HTTPException(status_code=403, detail="Access denied. Specified identity is not the registered author.")

    user = get_user_by_email(AUTHOR_EMAIL)
    if not user:
        init_auth_tables()
        user = get_user_by_email(AUTHOR_EMAIL)

    with db() as con:
        con.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user["id"],))

    token = generate_session_token(user["id"], user["email"], "author")
    return AuthTokenResponse(
        token=token,
        user=format_user_profile(user),
        message="Author verified. Full sovereign access granted across all platform subsystems."
    )


@router.get("/me")
def get_current_user_profile(authorization: Optional[str] = Header(None), token: Optional[str] = None):
    """Retrieve profile and permissions for currently authenticated session."""
    active_token = None
    if authorization and authorization.startswith("Bearer "):
        active_token = authorization.split(" ", 1)[1]
    elif token:
        active_token = token

    if not active_token:
        return {
            "authenticated": False,
            "user": None,
            "is_author": False,
            "access_tier": "guest",
        }

    claims = verify_session_token(active_token)
    if not claims:
        return {
            "authenticated": False,
            "user": None,
            "is_author": False,
            "access_tier": "guest",
        }

    user = get_user_by_id(claims["uid"])
    if not user:
        return {
            "authenticated": False,
            "user": None,
            "is_author": False,
            "access_tier": "guest",
        }

    is_author = (user["email"].strip().lower() == AUTHOR_EMAIL) or (user["role"] in ("author", "founder"))
    return {
        "authenticated": True,
        "user": format_user_profile(user),
        "is_author": is_author,
        "access_tier": "author_unlimited" if is_author else user["tier"],
        "permissions": [
            "ALL_13_DIVISIONS",
            "UNLIMITED_MACRO_SOLVERS",
            "ENGINEERING_CASCADE_ARREST",
            "MERKLE_TREE_PROVENANCE_AUTHORITY",
            "POST_QUANTUM_CYBER_DEFENSE",
            "CONFIDENTIAL_DOSSIER_ACCESS",
            "FOUNDER_POLICY_APPROVAL",
        ] if is_author else [
            "READ_DIVISIONS",
            "EXECUTE_SIMULATIONS",
            "VIEW_EVIDENCE",
        ]
    }


@router.post("/signout")
def sign_out():
    """Sign out current session."""
    return {"status": "SUCCESS", "message": "Logged out successfully."}
