def test_debt_simulation_baseline_identity(client):
    # When interest rate equals nominal growth and primary surplus is 0, debt-to-GDP ratio remains constant
    res = client.post("/api/modelling/debt/simulate", json={
        "initial_debt_percent_gdp": 100.0,
        "interest_rate_percent": 5.0,
        "nominal_gdp_growth_percent": 5.0,
        "primary_surplus_percent_gdp": 0.0,
        "foreign_debt_share_percent": 0.0,
        "currency_depreciation_percent": 0.0,
        "contingent_liabilities_percent_gdp": 0.0,
        "years": 4
    })
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    assert "baseline" in data["scenarios"]
    assert all(row["debt_percent_gdp"] == 100.0 for row in data["scenarios"]["baseline"])
    assert data["interest_growth_differential"] == 0.0


def test_debt_simulation_depreciation_and_consolidation(client):
    res = client.post("/api/modelling/debt/simulate", json={
        "initial_debt_percent_gdp": 80.0,
        "interest_rate_percent": 7.0,
        "nominal_gdp_growth_percent": 4.0,
        "primary_surplus_percent_gdp": 1.0,
        "foreign_debt_share_percent": 50.0,
        "currency_depreciation_percent": 20.0,
        "years": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert "adverse_shock" in data["scenarios"]
    assert "fiscal_consolidation" in data["scenarios"]
    assert "restructuring_reform" in data["scenarios"]
    # Restructuring should yield lower debt than adverse shock
    final_shock = data["scenarios"]["adverse_shock"][-1]["debt_percent_gdp"]
    final_reform = data["scenarios"]["restructuring_reform"][-1]["debt_percent_gdp"]
    assert final_reform < final_shock


def test_bad_debt_growth_rejected(client):
    res = client.post("/api/modelling/debt/simulate", json={
        "initial_debt_percent_gdp": 100.0,
        "interest_rate_percent": 5.0,
        "nominal_gdp_growth_percent": -100.0,
        "primary_surplus_percent_gdp": 0.0,
        "years": 3
    })
    assert res.status_code == 422
