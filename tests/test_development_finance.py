def test_development_finance_allocation_engine(client):
    res = client.post("/api/modelling/development-finance/simulate", json={
        "total_financing_pool_million_usd": 3000.0,
        "country_gdp_million_usd": 120000.0,
        "annual_govt_revenue_million_usd": 20000.0,
        "current_annual_debt_service_million_usd": 4000.0,
        "infrastructure_weight": 40.0,
        "healthcare_weight": 30.0,
        "education_weight": 15.0,
        "climate_adaptation_weight": 15.0,
        "concessional_interest_rate_percent": 1.5,
        "grant_element_share_percent": 40.0,
        "loan_maturity_years": 25
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_financing_pool_million_usd"] == 3000.0
    assert data["grant_amount_million_usd"] == 1200.0  # 40% of 3000
    assert data["concessional_loan_amount_million_usd"] == 1800.0
    assert "sector_allocations" in data
    assert "infrastructure" in data["sector_allocations"]
    assert "healthcare" in data["sector_allocations"]
    assert data["composite_weighted_multiplier"] > 1.0
    assert "debt_service_to_revenue_percent" in data
    assert "sustainability_rating" in data
