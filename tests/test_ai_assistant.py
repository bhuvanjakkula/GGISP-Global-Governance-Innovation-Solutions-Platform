def test_ai_draft_consent_gate(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "ai-governance",
        "title": "Frontier AI Safety Verification",
        "problem": "How can multilateral safety covenants verify algorithmic risk bounds?"
    }).json()
    pid = proj["id"]

    # Must reject without explicit consent confirmation
    res_no_consent = client.post(f"/api/projects/{pid}/ai-draft", json={
        "confirmed_external_ai_transfer": False
    })
    assert res_no_consent.status_code == 400


def test_ai_draft_synthesis_fallback(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "ai-governance",
        "title": "Frontier AI Safety Verification",
        "problem": "How can multilateral safety covenants verify algorithmic risk bounds?"
    }).json()
    pid = proj["id"]

    # When OPENAI_API_KEY is not configured, fallback heuristic synthesis runs safely
    res = client.post(f"/api/projects/{pid}/ai-draft", json={
        "confirmed_external_ai_transfer": True
    })
    assert res.status_code == 200
    data = res.json()
    assert "output_text" in data
    assert "label" in data
    assert "AI-generated" in data["label"]
    assert "PRELIMINARY RESEARCH SYNTHESIS" in data["output_text"]
