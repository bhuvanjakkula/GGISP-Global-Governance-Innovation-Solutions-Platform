def test_recommendation_and_approval_gate(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "sovereign-debt",
        "title": "Sovereign Debt Reprofiling Framework",
        "problem": "How can terms-of-trade indexation improve sovereign debt sustainability?"
    }).json()
    pid = proj["id"]

    rec = client.post(f"/api/projects/{pid}/recommendations", json={
        "recommendation": "Integrate natural disaster clauses into sovereign debt contracts.",
        "rationale": "Prevents catastrophic balance-of-payments crises following climate disasters.",
        "risks": "Requires standard documentation consensus among private London/NY law creditors.",
        "author": "Founder"
    }).json()
    rid = rec["id"]
    assert rec["approval_status"] == "draft"

    # Cannot approve without human confirmation flag
    fail_no_confirm = client.post(f"/api/recommendations/{rid}/approve", json={
        "confirmed_human_review": False
    })
    assert fail_no_confirm.status_code == 400

    # Cannot approve without at least one supported, manually reviewed claim
    fail_no_evidence = client.post(f"/api/recommendations/{rid}/approve", json={
        "confirmed_human_review": True
    })
    assert fail_no_evidence.status_code == 400

    # Now add reviewed source and supported claim
    src = client.post(f"/api/projects/{pid}/sources", json={
        "title": "IMF Policy Paper on Climate Resilient Debt Clauses",
        "url": "https://www.imf.org/en/Publications/Policy-Papers",
        "publisher": "IMF",
        "manually_reviewed": True
    }).json()

    client.post(f"/api/projects/{pid}/claims", json={
        "statement": "Climate-resilient debt clauses defer debt service by up to 24 months after certified shocks.",
        "evidence_status": "supported",
        "source_id": src["id"]
    })

    # Now approval succeeds
    success = client.post(f"/api/recommendations/{rid}/approve", json={
        "confirmed_human_review": True
    })
    assert success.status_code == 200
    assert success.json()["approval_status"] == "approved"

    # Project status promoted to 'ready'
    p_detail = client.get(f"/api/projects/{pid}").json()
    assert p_detail["status"] == "ready"
    assert len(p_detail["audit_log"]) > 0


def test_get_all_approved_guidance(client):
    res = client.get("/api/guidance/approved")
    assert res.status_code == 200
    data = res.json()
    assert data["total_approved"] >= 12
    assert "Bhuvan Jakkula" in data["founder_name"]
    assert data["founder_contact"] == "bjtmusic12@gmail.com"
    assert len(data["guidance"]) >= 12
    for item in data["guidance"]:
        assert item["approval_status"] == "approved"
        assert len(item["recommendation"]) > 10
        assert item["author"] == "Founder"
