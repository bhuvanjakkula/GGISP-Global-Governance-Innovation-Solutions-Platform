def test_brief_export_markdown(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "climate-finance",
        "title": "Loss and Damage Adaptation Architecture",
        "problem": "Designing transparent capital allocation for vulnerable small island developing states.",
        "country_code": "GLOBAL"
    }).json()
    pid = proj["id"]

    # Add source with hash
    src = client.post(f"/api/projects/{pid}/sources", json={
        "title": "UNFCCC Standing Committee on Finance Report",
        "url": "https://unfccc.int/topics/climate-finance",
        "publisher": "UNFCCC",
        "publication_year": 2024,
        "manually_reviewed": True,
        "quality_rating": "high"
    }).json()

    # Add claim
    client.post(f"/api/projects/{pid}/claims", json={
        "statement": "Annual adaptation finance flows represent less than 20% of estimated climate damage needs.",
        "evidence_status": "supported",
        "source_id": src["id"]
    })

    # Add recommendation
    rec = client.post(f"/api/projects/{pid}/recommendations", json={
        "recommendation": "Establish a multilateral parametric insurance pool capitalization target.",
        "rationale": "Parametric triggers release liquidity within 72 hours of catastrophic weather events.",
        "risks": "Requires accurate satellite meteorological indexing to eliminate basis risk.",
        "author": "Founder"
    }).json()

    # Approve
    client.post(f"/api/recommendations/{rec['id']}/approve", json={"confirmed_human_review": True})

    # Download brief
    brief = client.get(f"/api/projects/{pid}/brief.md")
    assert brief.status_code == 200
    text = brief.text
    assert "# GGISP Policy Research Brief" in text
    assert "Loss and Damage Adaptation Architecture" in text
    assert "UNFCCC" in text
    assert "Parametric triggers" in text
    assert "Institutional Submission & Governance Checklist" in text
    assert "SHA-256" in text
