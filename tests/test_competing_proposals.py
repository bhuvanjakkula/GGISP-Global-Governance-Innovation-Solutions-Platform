def test_competing_proposals_creation(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "nuclear-security",
        "title": "Multilateral Safeguards Verification Verification",
        "problem": "Evaluating peaceful verification technologies under IAEA safeguards agreements."
    }).json()
    pid = proj["id"]

    res = client.post(f"/api/projects/{pid}/competing-proposals", json={
        "proposal_title": "Unilateral National Verification Inspections",
        "proponent_summary": "Relying on bilateral sovereign intelligence and surveillance.",
        "trade_offs": "Lacks multilateral legitimacy; raises verification disputes among non-allied signatories.",
        "fiscal_impact": "High national defense expenditures.",
        "legal_feasibility": "Low adherence under NPT Article III."
    })
    assert res.status_code == 201
    assert "id" in res.json()

    p_detail = client.get(f"/api/projects/{pid}").json()
    assert len(p_detail["competing_proposals"]) == 1
    assert p_detail["competing_proposals"][0]["proposal_title"] == "Unilateral National Verification Inspections"


def test_save_simulation_to_project(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "sovereign-debt",
        "title": "Simulation Archival Test",
        "problem": "Testing the persistence of mathematical models in research dossiers."
    }).json()
    pid = proj["id"]

    sim_res = client.post(f"/api/projects/{pid}/save-simulation", json={
        "model_type": "debt_sustainability",
        "scenario_name": "Baseline Debt Path 2024-2029",
        "parameters": {"initial_debt": 70.0, "interest": 6.0},
        "results": {"final_debt": 68.5}
    })
    assert sim_res.status_code == 200
    assert sim_res.json()["status"] == "saved"

    p_detail = client.get(f"/api/projects/{pid}").json()
    assert len(p_detail["simulations"]) == 1


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert data["domains_count"] == 13
