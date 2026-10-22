"""Tests for Pricing Models, 2-Month Free Trial Offer, and Customer Enquiries."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ggisp.main import app
from ggisp.pricing import SUPPORT_CONTACT_EMAIL, init_enquiries_table

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_enquiries():
    init_enquiries_table()


def test_get_pricing_plans_includes_2_months_free_trial():
    res = client.get("/api/pricing/plans")
    assert res.status_code == 200
    data = res.json()
    assert "2 MONTHS FREE TRIAL" in data["special_offer"]
    assert data["support_contact"] == SUPPORT_CONTACT_EMAIL
    assert len(data["plans"]) == 3
    for plan in data["plans"]:
        assert plan["free_trial_months"] == 2
        assert "free trial" in plan["badge"].lower()
        assert plan["monthly_price_usd"] > 0

    sovereign = [p for p in data["plans"] if p["id"] == "sovereign"][0]
    assert sovereign["monthly_price_usd"] == 25000
    assert sovereign["stripe_payment_url"] == "https://buy.stripe.com/test_3cI9AL7qX2290gV2hVcjS0A"

    academic = [p for p in data["plans"] if p["id"] == "researcher"][0]
    assert academic["monthly_price_usd"] == 490
    assert academic["stripe_payment_url"] == "https://buy.stripe.com/test_28E14f26D7mt5BfbSvcjS0y"

    enterprise = [p for p in data["plans"] if p["id"] == "enterprise"][0]
    assert enterprise["monthly_price_usd"] == 2450
    assert enterprise["stripe_payment_url"] == "https://buy.stripe.com/test_7sY4gr6mT0Y5fbP2hVcjS0z"


def test_submit_customer_enquiry_success():
    payload = {
        "full_name": "Ambassador Elena Rostova",
        "email": "elena.rostova@diplomacy.int",
        "mobile_number": "+41 22 917 1234",
        "organization": "European Policy Council",
        "selected_plan": "enterprise",
        "message": "We would like to activate the 2-month free trial for our international sovereign debt risk team."
    }
    res = client.post("/api/pricing/enquiries", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["support_email"] == "bjtmusic12@gmail.com"
    assert data["free_trial_activated"] is True
    assert "60 Days" in data["free_trial_duration"]


def test_submit_customer_enquiry_invalid_email():
    payload = {
        "full_name": "Test User",
        "email": "not-an-email",
        "message": "Testing invalid email"
    }
    res = client.post("/api/pricing/enquiries", json=payload)
    assert res.status_code == 400


def test_list_customer_enquiries():
    res = client.get("/api/pricing/enquiries")
    assert res.status_code == 200
    data = res.json()
    assert "enquiries" in data
    assert data["support_inbox"] == "bjtmusic12@gmail.com"
