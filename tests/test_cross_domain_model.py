def test_cross_domain_simulation(client):
    res = client.post("/api/modelling/cross-domain/simulate", json={
        "country_code": "KEN",
        "country_name": "Kenya",
        "initial_debt_percent_gdp": 70.0,
        "baseline_gdp_growth_percent": 5.0,
        "baseline_interest_rate_percent": 7.0,
        "primary_balance_percent_gdp": -1.0,
        "annual_exports_million_usd": 7500.0,
        "trade_openness_percent_gdp": 35.0,
        "partner_tariff_shock_delta_pp": 6.0,
        "annual_concessional_finance_million_usd": 1500.0,
        "years": 5
    })
    assert res.status_code == 200
    data = res.json()
    assert "policy_paths" in data
    paths = data["policy_paths"]
    assert "path_1_austerity_status_quo" in paths
    assert "path_2_uncoordinated_haircut" in paths
    assert "path_3_ggisp_multilateral_accord" in paths

    p1 = paths["path_1_austerity_status_quo"]
    p3 = paths["path_3_ggisp_multilateral_accord"]

    # GGISP Accord should achieve lower debt and higher essential spending than austerity
    assert p3["final_debt_percent_gdp"] < p1["final_debt_percent_gdp"]
    assert p3["final_spending_index"] > p1["final_spending_index"]
    assert "trade_shock_summary" in data
