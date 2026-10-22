"""Pricing Models, 2-Month Free Trial Offer, and Customer Enquiries Service."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ggisp.db import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pricing", tags=["Pricing & Customer Enquiries"])

SUPPORT_CONTACT_EMAIL = "bjtmusic12@gmail.com"

PRICING_PLANS = [
    {
        "id": "researcher",
        "name": "Academic & Research Tier",
        "badge": "2 MONTHS FREE TRIAL",
        "free_trial_months": 2,
        "monthly_price_usd": 490,
        "annual_discount_percent": 20,
        "description": "Designed for independent policy institutes, universities, and non-profit think tanks.",
        "features": [
            "Access to all 13 Multilateral Research Divisions",
            "Cryptographic SHA-256 evidence source verification",
            "100 policy simulations per month",
            "Official multilateral data imports (World Bank, IMF, UN)",
            "Founder-reviewed policy advisory guidance access",
            "Standard email support via bjtmusic12@gmail.com",
        ],
        "target_audience": "Academic researchers, NGOs, and policy fellows",
        "cta_label": "Start 2-Month Free Trial",
    },
    {
        "id": "enterprise",
        "name": "Institutional & Enterprise Tier",
        "badge": "MOST POPULAR • 2 MONTHS FREE TRIAL",
        "free_trial_months": 2,
        "monthly_price_usd": 2450,
        "annual_discount_percent": 25,
        "description": "Full-spectrum quantitative policy workbench for commercial enterprises, sovereign wealth funds, and risk advisories.",
        "features": [
            "Everything in Academic Tier",
            "Full suite of 20 Quantitative Analytical Engines",
            "Non-linear Planetary Cascade Solvers with Pareto-Optimal Capital Allocation",
            "NIST FIPS 203/204/205 Post-Quantum Envelope Encryption (AES-256-GCM + ML-KEM-768)",
            "Operational Machine Playbook Generator (WTO, ICMA, CCSDS, FHIR)",
            "Multi-scenario comparative lab and sensitivity sweeps",
            "Priority 24/7 technical and methodology support",
        ],
        "target_audience": "Multinational corporations, banks, sovereign funds, and global consultancies",
        "cta_label": "Start 2-Month Free Trial",
    },
    {
        "id": "sovereign",
        "name": "Sovereign & Multilateral Alliance",
        "badge": "CUSTOM ONBOARDING • 2 MONTHS FREE TRIAL",
        "free_trial_months": 2,
        "monthly_price_usd": 25000,
        "annual_discount_percent": 30,
        "description": "Air-gapped and sovereign-grade deployment for national governments, ministries, and treaty secretariats.",
        "features": [
            "Everything in Enterprise Tier",
            "Custom sovereign deployment with private cryptographic key escrow",
            "Bespoke Shor algorithm quantum threat modeling for state secrets",
            "Direct strategic advisory channel with Platform Founder",
            "Custom mathematical econometric and contagion modules",
            "Unlimited simulation throughput and SLA guarantees",
            "Dedicated executive account manager & hotline",
        ],
        "target_audience": "Ministries of finance, foreign affairs, central banks, and UN agencies",
        "cta_label": "Request Sovereign Onboarding",
    },
]


class EnquiryRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=150)
    mobile_number: Optional[str] = Field(default="", max_length=30)
    organization: Optional[str] = Field(default="", max_length=150)
    selected_plan: str = Field(default="enterprise")
    message: str = Field(..., min_length=5, max_length=2000)


def init_enquiries_table() -> None:
    """Ensure customer enquiries table exists in SQLite database."""
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS customer_enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            mobile_number TEXT NOT NULL DEFAULT '',
            organization TEXT NOT NULL DEFAULT '',
            selected_plan TEXT NOT NULL,
            message TEXT NOT NULL,
            support_recipient TEXT NOT NULL DEFAULT 'bjtmusic12@gmail.com',
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)


@router.get("/plans")
def get_plans():
    """Retrieve all available subscription plans with 2-month free trial details."""
    return {
        "special_offer": "2 MONTHS FREE TRIAL ON ALL TIERS",
        "offer_terms": "Full access to all platform features for 60 days with zero upfront commitment. Cancel anytime.",
        "support_contact": SUPPORT_CONTACT_EMAIL,
        "plans": PRICING_PLANS,
    }


@router.post("/enquiries")
def submit_enquiry(req: EnquiryRequest):
    """Submit customer enquiry, support request, or trial activation."""
    email_clean = req.email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email_clean):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    init_enquiries_table()

    with db() as con:
        cur = con.execute("""
            INSERT INTO customer_enquiries (full_name, email, mobile_number, organization, selected_plan, message, support_recipient)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            req.full_name.strip(),
            email_clean,
            (req.mobile_number or "").strip(),
            (req.organization or "").strip(),
            req.selected_plan.strip(),
            req.message.strip(),
            SUPPORT_CONTACT_EMAIL,
        ))
        enquiry_id = cur.lastrowid

    logger.info(f"New customer enquiry #{enquiry_id} received from {email_clean} routed to {SUPPORT_CONTACT_EMAIL}")

    return {
        "status": "SUCCESS",
        "enquiry_id": enquiry_id,
        "message": f"Thank you, {req.full_name}. Your enquiry for the {req.selected_plan} plan (with 2 Months Free Trial) has been received. Our team will contact you shortly at {email_clean}. You may also reach us directly at {SUPPORT_CONTACT_EMAIL}.",
        "support_email": SUPPORT_CONTACT_EMAIL,
        "free_trial_activated": True,
        "free_trial_duration": "60 Days (2 Months)",
    }


@router.get("/enquiries")
def list_enquiries(limit: int = Query(default=50, ge=1, le=200)):
    """Retrieve submitted customer enquiries (administrative view)."""
    init_enquiries_table()
    with db() as con:
        cur = con.execute("SELECT * FROM customer_enquiries ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        return {
            "total_enquiries": len(rows),
            "support_inbox": SUPPORT_CONTACT_EMAIL,
            "enquiries": rows,
        }
