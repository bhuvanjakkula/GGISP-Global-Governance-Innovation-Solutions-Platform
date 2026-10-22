"""Specialist Engine 13: Climate Finance, Parametric Disaster Loss, & Adaptation Accounting Engine.
Reference: UNFCCC Enhanced Transparency Framework (ETF) / Paris Agreement Art. 6 / OECD CRS Adaptation Tracking.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ClimateParametricInput(BaseModel):
    hazard_type: str = Field(default="tropical_cyclone_windspeed", description="Hazard: tropical_cyclone_windspeed, drought_rainfall_deficit, coastal_flood_surge")
    maximum_parametric_coverage_million_usd: float = Field(default=120.0, ge=5.0, le=2000.0)
    parametric_trigger_threshold_knots: float = Field(default=95.0, ge=64.0, le=160.0, description="Windspeed trigger in knots (Category 3+)")
    catastrophe_exhaustion_threshold_knots: float = Field(default=135.0, ge=100.0, le=200.0, description="Full 100% payout windspeed")
    recorded_event_intensity_knots: float = Field(default=115.0, ge=50.0, le=220.0, description="Satellite certified event windspeed")
    article_6_itmo_credits_tonnes_co2e: float = Field(default=2500000.0, ge=1000.0, le=100000000.0, description="High-integrity mitigation credits")
    carbon_credit_price_per_tonne_usd: float = Field(default=35.0, ge=5.0, le=250.0)
    days_to_guaranteed_payout: int = Field(default=5, ge=1, le=14, description="Parametric liquidity release window")

    # Adaptation Finance Accounting & Overreporting Auditing (Donner et al. 2016; Borst et al. 2023; De Aguiar et al. 2024)
    adaptation_finance_accounting_modality: str = Field(
        default="grant_equivalent_strict_additionality",
        description="Accounting standard: donor_self_reported_face_value, grant_equivalent_strict_additionality, broad_discretionary_rio_markers"
    )
    reported_adaptation_commitment_million_usd: float = Field(
        default=60.0,
        ge=0.0,
        le=5000.0,
        description="Gross headline adaptation funding commitment reported by bilateral/multilateral donor"
    )
    loan_concessionality_grant_element_percent: float = Field(
        default=42.0,
        ge=0.0,
        le=100.0,
        description="Grant-equivalent element % of loan tranches (De Aguiar et al. 2024; Bergsvik et al. 2024)"
    )
    oda_additionality_recycling_percent: float = Field(
        default=78.0,
        ge=0.0,
        le=100.0,
        description="Share of climate aid re-tagged/recycled from existing ODA budgets (Khan et al. 2019)"
    )
    nlp_overreporting_discount_percent: float = Field(
        default=32.03,
        ge=0.0,
        le=70.0,
        description="Empirical Bayesian text-classification overreporting discount rate % (Borst et al. 2023)"
    )


def simulate_climate_parametric(inp: ClimateParametricInput) -> Dict[str, Any]:
    """Calculate parametric disaster liquidity, Article 6 carbon revenue, and audit adaptation finance accounting integrity."""
    t_start = inp.parametric_trigger_threshold_knots
    t_max = inp.catastrophe_exhaustion_threshold_knots
    actual = inp.recorded_event_intensity_knots

    # Linear parametric payout scaling between trigger and exhaustion:
    if actual < t_start:
        payout_ratio = 0.0
    elif actual >= t_max:
        payout_ratio = 1.0
    else:
        payout_ratio = (actual - t_start) / (t_max - t_start)

    emergency_payout_million = inp.maximum_parametric_coverage_million_usd * payout_ratio

    # Article 6.2/6.4 ITMO carbon revenue generation:
    carbon_revenue_gross_million = (inp.article_6_itmo_credits_tonnes_co2e * inp.carbon_credit_price_per_tonne_usd) / 1e6
    sop_adaptation_fund_deduction_million = carbon_revenue_gross_million * 0.05
    net_sovereign_carbon_revenue_million = carbon_revenue_gross_million - sop_adaptation_fund_deduction_million

    # Combined climate fiscal liquidity:
    total_immediate_liquidity_million = emergency_payout_million + net_sovereign_carbon_revenue_million

    # Adaptation Finance Accounting & Overreporting Audit (Borst et al. 2023; Donner et al. 2016; De Aguiar et al. 2024):
    reported_gross = inp.reported_adaptation_commitment_million_usd
    modality = inp.adaptation_finance_accounting_modality.lower().strip()

    if modality == "grant_equivalent_strict_additionality":
        # Deflate for NLP text-classification overreporting, apply grant-equivalency, and deduct recycled ODA
        deflated_volume = reported_gross * (1.0 - inp.nlp_overreporting_discount_percent / 100.0)
        grant_equiv = deflated_volume * (inp.loan_concessionality_grant_element_percent / 100.0)
        genuine_additional_grant_equivalent_million = grant_equiv * (1.0 - (inp.oda_additionality_recycling_percent * 0.5) / 100.0)
        overreporting_gap_percent = round((1.0 - (genuine_additional_grant_equivalent_million / reported_gross)) * 100.0, 1) if reported_gross > 0 else 0.0
        accounting_status = "STRICT GRANT-EQUIVALENCY: Strips out non-concessional loan principal, recycled ODA, and epistemic Rio marker over-tagging (Borst et al. 2023; De Aguiar et al. 2024)."
    elif modality == "broad_discretionary_rio_markers":
        genuine_additional_grant_equivalent_million = reported_gross * 0.55
        overreporting_gap_percent = 45.0
        accounting_status = "BROAD DISCRETIONARY RIO MARKERS: Co-benefits and secondary links inflated into adaptation headline totals (Donner et al. 2016; Savvidou et al. 2021)."
    else:  # donor_self_reported_face_value
        genuine_additional_grant_equivalent_million = reported_gross
        overreporting_gap_percent = 0.0
        accounting_status = "DONOR SELF-REPORTED FACE VALUE (STATUS QUO): Full loan face values and re-tagged ODA counted without grant-equivalent adjustment (Bergsvik et al. 2024)."

    # Core Accounting Dimensions Driving Reporting Divergence Matrix (Figure 2 Synthesis):
    accounting_dimensions_matrix = [
        {
            "accounting_dimension": "Financial Instruments",
            "dominant_reporting_modalities": "Full face value of loans versus grant-equivalent values (De Aguiar et al. 2024; Bergsvik et al. 2024)",
            "impact_on_reported_figures": "Substantially inflates aggregate headline figures using non-concessional debt (Savvidou et al. 2021; Venner et al. 2024)",
            "effect_on_comparability": "Obscures actual net resource transfers and penalizes grant-providing nations (De Aguiar et al. 2024)"
        },
        {
            "accounting_dimension": "Additionality Criteria",
            "dominant_reporting_modalities": "Re-tagging existing official development assistance (ODA) (Khan et al. 2019)",
            "impact_on_reported_figures": "Diverts basic development assistance into apparent climate flows (76-80% recycled) (Khan et al. 2019)",
            "effect_on_comparability": "Distorts whether donors deliver genuinely new and additional public capital (Khan et al. 2019)"
        },
        {
            "accounting_dimension": "Thematic Attribution",
            "dominant_reporting_modalities": "Discretionary Rio marking ('significant' vs 'principal') (Donner et al. 2016; Savvidou et al. 2021)",
            "impact_on_reported_figures": "Overstates funding via broad co-benefit and cross-cutting allocations (De Développement et al. 2012)",
            "effect_on_comparability": "Prevents reliable tracking between pure adaptation and mitigation interventions (Xu et al. 2016)"
        },
        {
            "accounting_dimension": "Private Co-Financing",
            "dominant_reporting_modalities": "Unstandardized gross versus net mobilization accounting (Stadelmann et al. 2013)",
            "impact_on_reported_figures": "Artificially expands reported resilience figures using highly unverified ranges (Pauw et al. 2016)",
            "effect_on_comparability": "Generates non-comparable claims across multilateral and bilateral donors (Stadelmann et al. 2013)"
        }
    ]

    return {
        "engine": "Loss and Damage Parametric Disaster Trigger & Adaptation Finance Accounting Engine",
        "domain": "climate-finance",
        "hazard_type": inp.hazard_type,
        "parametric_trigger_breached": actual >= t_start,
        "payout_intensity_fraction_percent": round(payout_ratio * 100.0, 1),
        "emergency_disaster_liquidity_payout_million_usd": round(emergency_payout_million, 2),
        "payout_timeline_days": inp.days_to_guaranteed_payout,
        "article_6_carbon_revenue_net_million_usd": round(net_sovereign_carbon_revenue_million, 2),
        "total_available_climate_fiscal_headroom_million_usd": round(total_immediate_liquidity_million, 2),
        "adaptation_finance_accounting_audit": {
            "accounting_modality": inp.adaptation_finance_accounting_modality,
            "reported_headline_commitment_million_usd": round(reported_gross, 2),
            "genuine_grant_equivalent_additionality_million_usd": round(genuine_additional_grant_equivalent_million, 2),
            "overreporting_inflation_gap_percent": overreporting_gap_percent,
            "accounting_integrity_assessment": accounting_status,
            "empirical_case_evidence": {
                "oceania_discretionary_spread": "Adaptation represented only 3-4% under explicit definitions, but exploded to 37% under broad discretionary assumptions (Donner et al. 2016).",
                "adb_multilateral_audit": "Independent portfolio assessment of Asian Development Bank identified overstatements averaging 44% of reported commitments (Acharya et al. 2024).",
                "oda_recycling_prevalence": "76% to 80% of reported adaptation finance is recycled from existing official development assistance budgets (Khan et al. 2019)."
            },
            "comparability_dimensions_matrix": accounting_dimensions_matrix,
            "unfccc_enhanced_transparency_framework": "Under Paris Agreement ETF, grant-equivalency reporting remains voluntary, leaving cross-country donor comparability severely distorted (Bergsvik et al. 2024; Weikmans & Roberts 2019)."
        },
        "fund_activation_status": (
            f"PARAMETRIC DISASTER TRIGGER ACTIVATED: Emergency disbursement of ${round(emergency_payout_million, 1)}M released within {inp.days_to_guaranteed_payout} days."
            if emergency_payout_million > 0
            else "BELOW PARAMETRIC THRESHOLD: No catastrophic emergency release triggered."
        ),
        "treaty_reference": "UNFCCC COP28 Loss & Damage Fund, Paris Agreement Article 6.2/6.4, & Enhanced Transparency Framework (ETF).",
        "literature_citations": [
            "Acharya, S. et al. (2024). Unaccountable Adaptation: Asian Development Bank's overstated claims. Oxfam, 10.21201/2024.000023",
            "Bergsvik, R. et al. (2024). Is transparency furthering clarity in climate finance?. Int. Environ. Agreements, 10.1007/s10784-024-09652-y",
            "Borst, J. et al. (2023). Credible Estimation for Overreporting of Climate Adaptation Funds. LaTeCH-CLfL, 10.18653/v1/2023.latechclfl-1.11",
            "De Aguiar, T. S. D. et al. (2024). Mapping accounting literature on climate finance. Account. Res. J., 10.1108/arj-06-2023-0162",
            "De Développement, B. I. et al. (2012). Joint MDB Report on Adaptation Finance 2011. IDB, 10.18235/0006466",
            "Donner, S. et al. (2016). Measuring and tracking flow of adaptation aid. Environ. Res. Lett., 10.1088/1748-9326/11/5/054006",
            "Hall, N. (2017). What is adaptation? Epistemic ambiguity in climate finance. Int. Environ. Agreements, 10.1007/s10784-016-9345-6",
            "Isah, A. et al. (2025). Quantifying climate finance needs in NDCs of developing countries. Clim. Policy, 10.1080/14693062.2025.2460607",
            "Khan, M. R. et al. (2019). Twenty-five years of adaptation finance through climate justice lens. Clim. Change, 10.1007/s10584-019-02563-x",
            "Pauw, W. et al. (2016). Private finance for adaptation: public ambitions. Clim. Change, 10.1007/s10584-015-1539-3",
            "Roberts, J., & Weikmans, R. (2017). Fragmentation and failing trust over what counts as climate finance. Int. Environ. Agreements, 10.1007/s10784-016-9347-4",
            "Savvidou, G. et al. (2021). Quantifying international public finance for adaptation in Africa. Clim. Policy, 10.1080/14693062.2021.1978053",
            "Shishlov, I., & Censkowsky, P. (2022). Definitions and accounting of climate finance. Clim. Policy, 10.1080/14693062.2022.2080634",
            "Stadelmann, M. et al. (2013). Difficulties in accounting for private finance. Clim. Policy, 10.1080/14693062.2013.791146",
            "Venner, K. et al. (2024). Multi-Scalar Inequities of Adaptation Finance. Curr. Clim. Change Rep., 10.1007/s40641-024-00195-7",
            "Weikmans, R., & Roberts, J. (2019). International climate finance accounting muddle. Clim. Dev., 10.1080/17565529.2017.1410087",
            "Xu, Y.-S. et al. (2016). Establishing MRV system for climate finance. Chin. J. Popul. Resour. Environ., 10.1080/10042857.2016.1258802"
        ]
    }
