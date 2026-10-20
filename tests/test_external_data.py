def test_list_supported_countries(client):
    res = client.get("/api/external-data/countries")
    assert res.status_code == 200
    countries = res.json()
    assert len(countries) >= 7
    codes = [c["code"] for c in countries]
    assert "KEN" in codes
    assert "GHA" in codes
    assert "LKA" in codes
    assert "ARG" in codes


def test_unified_macro_profile_and_caching(client):
    res = client.get("/api/external-data/profile/KEN")
    assert res.status_code == 200
    data = res.json()
    assert data["country_code"] == "KEN"
    assert "world_bank" in data
    assert "imf" in data
    assert "wto" in data
    assert "calibrated_model_defaults" in data
    assert data["calibrated_model_defaults"]["initial_debt_percent_gdp"] > 0
    assert data["calibrated_model_defaults"]["base_exports_million_usd"] > 0
    assert data["provenance"]["is_multilateral_official"] is True


def test_wto_tariff_shock_calculation(client):
    from ggisp.external_data.wto import WTOClient
    wto = WTOClient()
    shock = wto.simulate_tariff_trade_shock(
        base_exports_usd=10000.0,
        base_tariff_percent=10.0,
        tariff_shock_delta_pp=5.0,
        price_elasticity_of_demand=-1.2
    )
    assert shock["export_revenue_loss_usd"] > 0
    assert shock["new_exports_usd"] < 10000.0
