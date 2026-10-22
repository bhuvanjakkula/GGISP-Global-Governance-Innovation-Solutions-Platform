def test_thirteen_domains_exist(client):
    res = client.get("/api/domains")
    assert res.status_code == 200
    domains = res.json()
    assert len(domains) == 13
    slugs = [d["slug"] for d in domains]
    assert "nuclear-security" in slugs
    assert "un-security-council" in slugs
    assert "wto-trade" in slugs
    assert "sovereign-debt" in slugs
    assert "ai-governance" in slugs
    assert "development-finance" in slugs
    assert "climate-finance" in slugs


def test_seed_demo_projects_available(client):
    res = client.get("/api/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 1
    assert any(p["domain_slug"] == "sovereign-debt" for p in projects)


def test_metrics_summary(client):
    res = client.get("/api/metrics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["divisions"] == 13
    assert data["projects"] >= 1
    assert "total_evidence" in data
    assert "approved_guidance" in data
    assert "total_simulations" in data

