def test_full_e2e_research_and_advisory_lifecycle(client):
    # 1. Browse 13 domains
    domains = client.get("/api/domains").json()
    assert len(domains) == 13

    # 2. Query official World Bank, IMF, WTO data
    macro = client.get("/api/external-data/profile/KEN").json()
    assert macro["country_code"] == "KEN"
    calibrated = macro["calibrated_model_defaults"]

    # 3. Create a project using calibrated country data
    proj = client.post("/api/projects", json={
        "domain_slug": "sovereign-debt",
        "title": "Kenya Sovereign Debt and WTO Trade Reform",
        "problem": "How can transparent restructuring protect development spending amidst tariff volatility?",
        "country_code": "KEN"
    }).json()
    pid = proj["id"]

    # 4. Run the 3 quantitative models
    debt_res = client.post("/api/modelling/debt/simulate", json={
        "initial_debt_percent_gdp": calibrated["initial_debt_percent_gdp"],
        "interest_rate_percent": calibrated["interest_rate_percent"],
        "nominal_gdp_growth_percent": calibrated["nominal_gdp_growth_percent"],
        "primary_surplus_percent_gdp": calibrated["primary_surplus_percent_gdp"],
        "years": 5
    }).json()
    assert len(debt_res["scenarios"]["baseline"]) == 6

    devfin_res = client.post("/api/modelling/development-finance/simulate", json={
        "total_financing_pool_million_usd": 2000.0,
        "country_gdp_million_usd": 115000.0,
        "annual_govt_revenue_million_usd": 19000.0,
        "current_annual_debt_service_million_usd": 4500.0,
        "infrastructure_weight": 35.0,
        "healthcare_weight": 25.0,
        "education_weight": 20.0,
        "climate_adaptation_weight": 20.0
    }).json()
    assert devfin_res["composite_sdg_impact_score_100"] > 50

    cross_res = client.post("/api/modelling/cross-domain/simulate", json={
        "country_code": "KEN",
        "initial_debt_percent_gdp": calibrated["initial_debt_percent_gdp"],
        "annual_exports_million_usd": calibrated["base_exports_million_usd"],
        "partner_tariff_shock_delta_pp": 4.5
    }).json()
    assert "policy_paths" in cross_res

    # 5. Save simulation to project
    client.post(f"/api/projects/{pid}/save-simulation", json={
        "model_type": "cross_domain_macro",
        "scenario_name": "Calibrated Kenya Macro Shock 2024",
        "parameters": calibrated,
        "results": cross_res
    })

    # 6. Record source and claim
    src = client.post(f"/api/projects/{pid}/sources", json={
        "title": "World Bank / IMF Joint Debt Sustainability Analysis",
        "url": "https://www.imf.org/en/Publications/CR",
        "publisher": "IMF / World Bank",
        "publication_year": 2024,
        "manually_reviewed": True,
        "quality_rating": "high"
    }).json()

    client.post(f"/api/projects/{pid}/claims", json={
        "statement": "Debt restructuring coupled with concessional financing lowers debt by 15 percent over 5 years.",
        "evidence_status": "supported",
        "source_id": src["id"]
    })

    # 7. Write and approve recommendation
    rec = client.post(f"/api/projects/{pid}/recommendations", json={
        "recommendation": "Execute a terms-of-trade linked sovereign debt reprofiling accord.",
        "rationale": "Prevents debt overhang and preserves capital budget for health and education.",
        "risks": "Requires multilateral creditor committee coordination under the G20 Common Framework.",
        "author": "Founder"
    }).json()

    approve_res = client.post(f"/api/recommendations/{rec['id']}/approve", json={"confirmed_human_review": True})
    assert approve_res.status_code == 200

    # 8. Export brief
    brief = client.get(f"/api/projects/{pid}/brief.md")
    assert brief.status_code == 200
    assert "Kenya Sovereign Debt and WTO Trade Reform" in brief.text
    assert "Founder" in brief.text
    assert "APPROVED" in brief.text
