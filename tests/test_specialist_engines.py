from ggisp.specialist_engines import (
    ENGINE_CATALOG,
    DebtBargainingInput,
    execute_specialist_engine,
    list_specialist_engines,
    simulate_debt_bargaining,
)



def test_engines_catalog_coverage():
    engines = list_specialist_engines()
    assert len(engines) == 13
    slugs = [e["domain_slug"] for e in engines]
    expected_slugs = [
        "nuclear-security", "un-security-council", "wto-trade", "sovereign-debt",
        "ai-governance", "cybersecurity", "global-health", "space-security",
        "critical-minerals", "ocean-governance", "international-tax",
        "development-finance", "climate-finance"
    ]
    for s in expected_slugs:
        assert s in slugs


def test_nuclear_safeguards_simulation():
    res = execute_specialist_engine("nuclear-security", {
        "product_enrichment_percent": 60.0,
        "target_weapons_grade_percent": 90.0,
        "cascade_separative_work_capacity_swu_yr": 15000.0,
        "current_stockpile_kg": 140.0
    })
    assert res["swu_required_per_significant_quantity"] > 0
    assert res["estimated_breakout_time_days"] > 0
    assert "safeguards_verification_protocol" in res
    assert res["zero_knowledge_warhead_verification"]["enabled"] is True
    assert "frontier_ai_escalation_benchmark" in res



def test_unsc_veto_simulation():
    res = execute_specialist_engine("un-security-council", {
        "resolution_type": "chapter_vii_sanctions",
        "e10_affirmative_votes": 8,
        "ru_veto_prob": 0.80,
        "cn_veto_prob": 0.40
    })
    assert res["meets_procedural_9_vote_rule"] is True
    assert res["probability_of_veto_blockage_percent"] > 50.0
    assert "shapley_shubik_power_distribution" in res
    assert "article_108_amendment_feasibility" in res


def test_unsc_reform_models():
    res = execute_specialist_engine("un-security-council", {
        "reform_model": "double_veto_rule",
        "ru_veto_prob": 0.80,
        "cn_veto_prob": 0.40
    })
    assert "Double Veto" in res["council_composition"]["veto_rule"]
    assert res["article_108_amendment_feasibility"]["ga_two_thirds_majority_secured"] is False



def test_wto_gravity_trade_simulation():
    res = execute_specialist_engine("wto-trade", {
        "exporter_gdp_billion_usd": 110.0,
        "importer_gdp_billion_usd": 19000.0,
        "distance_km": 7000.0,
        "has_free_trade_agreement": True,
        "applied_tariff_percent": 6.5,
        "chokepoint_exposure": "suez_and_bab_el_mandeb"
    })
    assert res["predicted_bilateral_trade_volume_billion_usd"] > 0
    assert res["annual_trade_value_at_risk_million_usd"] > 0


def test_sovereign_debt_stochastic_simulation():
    res = execute_specialist_engine("sovereign-debt", {
        "initial_debt_percent_gdp": 85.0,
        "baseline_interest_percent": 7.0,
        "baseline_growth_percent": 4.0,
        "monte_carlo_draws": 150
    })
    assert len(res["fan_chart_percentiles"]) == 6
    assert res["required_npv_haircut_percent_to_reach_target"] > 0
    assert "game_theoretic_bargaining" in res
    assert res["game_theoretic_bargaining"]["endogenous_nash_haircut_percent"] > 0


def test_debt_bargaining_game_simulation():
    res = simulate_debt_bargaining(DebtBargainingInput(
        country_code="KEN",
        outstanding_debt_percent_gdp=78.0,
        debtor_bargaining_power_theta=0.5,
        imf_program_liquidity_support_percent_gdp=7.0,
        is_preemptive_restructuring=True,
        incorporate_gdp_indexed_bonds=True,
        is_election_year=True,
        official_projected_5yr_debt_percent_gdp=69.0
    ))
    assert res["endogenous_nash_haircut_percent"] > 0
    assert res["imf_hjb_liquidity_yield_compression_bps"] > 0
    assert res["political_economy_forecast_correction"]["systemic_forecast_error_bias_pp"] > 5.0
    assert res["gdp_indexed_bonds"]["enabled"] is True
    assert "legal_framework_evaluation" in res
    assert res["legal_framework_evaluation"]["holdout_litigation_risk_percent"] < 10.0




def test_ai_frontier_governance_simulation():
    res = execute_specialist_engine("ai-governance", {
        "model_name": "Frontier-LLM-1T",
        "parameter_count_billions": 1000.0,
        "training_dataset_tokens_trillions": 20.0
    })
    assert res["exceeds_10_26_frontier_covenant_threshold"] is True
    assert "Systemic" in res["governance_classification"]


def test_cyber_defensive_simulation():
    res = execute_specialist_engine("cybersecurity", {
        "critical_infrastructure_sectors_protected": 12,
        "data_shelf_life_security_years": 20,
        "pqc_migration_duration_years": 8,
        "estimated_years_to_cryptanalytic_quantum": 10
    })
    assert res["national_cyber_resilience_index_100"] > 0
    assert res["mosca_quantum_theorem_evaluation"]["harvest_now_decrypt_later_vulnerability"] is True


def test_global_health_simulation():
    res = execute_specialist_engine("global-health", {
        "reproduction_number_r0": 2.5,
        "variant_immune_evasion_percent": 30.0,
        "simulation_days": 60
    })
    assert res["effective_reproduction_number_r_eff"] > 2.5
    assert res["estimated_critical_care_icu_demand"] > 0


def test_space_orbital_debris_simulation():
    res = execute_specialist_engine("space-security", {
        "satellite_altitude_km": 550.0,
        "conjunction_miss_distance_meters": 45.0
    })
    assert "collision_probability_p_c" in res
    assert res["collision_avoidance_maneuver_required"] is True


def test_critical_minerals_simulation():
    res = execute_specialist_engine("critical-minerals", {
        "mineral_type": "lithium",
        "top_country_market_share_percent": 70.0
    })
    assert res["herfindahl_hirschman_index_hhi"] > 2500
    assert "Highly Concentrated" in res["market_concentration_tier"]


def test_ocean_governance_simulation():
    res = execute_specialist_engine("ocean-governance", {
        "carrying_capacity_k_thousand_tons": 3000.0,
        "current_biomass_thousand_tons": 1200.0
    })
    assert res["maximum_sustainable_yield_msy_kt"] > 0
    assert res["total_harvest_including_iuu_kt"] > 0


def test_international_tax_simulation():
    res = execute_specialist_engine("international-tax", {
        "local_constituent_entity_profit_million_usd": 150.0,
        "covered_taxes_paid_million_usd": 12.0
    })
    assert res["effective_tax_rate_etr_percent"] < 15.0
    assert res["projected_top_up_tax_revenue_million_usd"] > 0


def test_blended_finance_simulation():
    res = execute_specialist_engine("development-finance", {
        "project_total_capex_million_usd": 400.0,
        "concessional_first_loss_grant_million_usd": 40.0,
        "target_commercial_senior_debt_million_usd": 240.0
    })
    assert "private_capital_mobilization_ratio" in res
    assert res["blended_weighted_average_cost_of_capital_percent"] < res["unblended_commercial_borrowing_cost_percent"]


def test_climate_parametric_simulation():
    res = execute_specialist_engine("climate-finance", {
        "maximum_parametric_coverage_million_usd": 100.0,
        "parametric_trigger_threshold_knots": 95.0,
        "recorded_event_intensity_knots": 120.0
    })
    assert res["parametric_trigger_breached"] is True
    assert res["emergency_disaster_liquidity_payout_million_usd"] > 0
