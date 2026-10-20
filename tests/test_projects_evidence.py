def test_create_project_and_validation(client):
    # Valid project
    res = client.post("/api/projects", json={
        "domain_slug": "wto-trade",
        "title": "Agricultural Tariff Impact on Food Security",
        "problem": "How do fluctuating agricultural tariffs affect food import security in developing countries?",
        "country_code": "KEN"
    })
    assert res.status_code == 201
    pid = res.json()["id"]

    # Invalid domain
    bad_res = client.post("/api/projects", json={
        "domain_slug": "non-existent-domain",
        "title": "Invalid Domain Test",
        "problem": "This should fail because domain does not exist in catalog."
    })
    assert bad_res.status_code == 400


def test_source_creation_with_hash(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "sovereign-debt",
        "title": "Debt Restructuring Evidence Test",
        "problem": "Investigating empirical debt restructuring benchmarks across emerging markets."
    }).json()
    pid = proj["id"]

    source_res = client.post(f"/api/projects/{pid}/sources", json={
        "title": "World Bank International Debt Report 2024",
        "url": "https://www.worldbank.org/en/publication/international-debt-report",
        "publisher": "World Bank",
        "publication_year": 2024,
        "notes": "Verified statistics on sovereign debt service to revenue ratios.",
        "manually_reviewed": True,
        "quality_rating": "high"
    })
    assert source_res.status_code == 201
    src_data = source_res.json()
    assert "content_hash" in src_data
    assert len(src_data["content_hash"]) == 64  # SHA-256


def test_source_url_rejects_non_http(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "cybersecurity",
        "title": "Cybersecurity Baseline Study",
        "problem": "Analyzing international incident response protocols under UN OEWG frameworks."
    }).json()
    pid = proj["id"]

    bad_url_res = client.post(f"/api/projects/{pid}/sources", json={
        "title": "Malicious Link Attempt",
        "url": "file:///etc/shadow",
        "publisher": "Unknown"
    })
    assert bad_url_res.status_code == 422


def test_supported_claim_requires_reviewed_source(client):
    proj = client.post("/api/projects", json={
        "domain_slug": "global-health",
        "title": "Global Vaccine Distribution Logistics",
        "problem": "Evaluating multilateral distribution mechanisms during epidemiological crises."
    }).json()
    pid = proj["id"]

    # Supported claim without source must fail
    res_no_src = client.post(f"/api/projects/{pid}/claims", json={
        "statement": "Vaccine distribution bottlenecks increase mortality by 12 percent.",
        "evidence_status": "supported"
    })
    assert res_no_src.status_code == 400

    # Add unreviewed source
    unreviewed_src = client.post(f"/api/projects/{pid}/sources", json={
        "title": "Draft Working Paper",
        "url": "https://example.org/draft-paper",
        "publisher": "Independent Thinktank",
        "manually_reviewed": False
    }).json()

    # Supported claim with unreviewed source must fail
    res_unreviewed_src = client.post(f"/api/projects/{pid}/claims", json={
        "statement": "Vaccine distribution bottlenecks increase mortality by 12 percent.",
        "evidence_status": "supported",
        "source_id": unreviewed_src["id"]
    })
    assert res_unreviewed_src.status_code == 400
