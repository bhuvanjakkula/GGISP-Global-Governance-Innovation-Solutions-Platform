"""Specialist Engine 12: Blended Finance Capital Stack, MDB Guarantees, & Capital Allocation Skew Engine.
Reference: OECD Blended Finance Principles / DFI Working Group / IFC Blended Concessional Finance (Flammer et al. 2024).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class BlendedFinanceInput(BaseModel):
    project_total_capex_million_usd: float = Field(default=500.0, ge=10.0, le=50000.0)
    concessional_first_loss_grant_million_usd: float = Field(default=50.0, ge=1.0, le=5000.0, description="De-risking anchor capital")
    multilateral_subordinated_loan_million_usd: float = Field(default=150.0, ge=0.0, le=20000.0, description="MDB concessional tranche")
    target_commercial_senior_debt_million_usd: float = Field(default=300.0, ge=0.0, le=30000.0, description="Private institutional debt")
    project_projected_economic_irr_percent: float = Field(default=14.5, ge=1.0, le=50.0)
    sovereign_credit_spread_bps: float = Field(default=450.0, ge=50.0, le=2500.0)

    # Development Finance Guarantees & Capital Allocation (Aitkazin et al. 2026; Matthäus & Mehling 2020; Flammer et al. 2024)
    enable_credit_guarantee_mechanism: bool = Field(
        default=True,
        description="MDB Partial Risk Guarantee (PRG) or political risk guarantee compressing private loan spreads (Aitkazin et al. 2026)"
    )
    guarantee_coverage_ratio_percent: float = Field(
        default=50.0,
        ge=10.0,
        le=100.0,
        description="Share of commercial senior debt covered by MDB/sovereign guarantee"
    )
    target_country_income_group: str = Field(
        default="middle_income",
        description="Host income tier: middle_income, frontier_fragile_state, advanced_emerging"
    )
    country_political_risk_z_score: float = Field(
        default=0.85,
        ge=-2.5,
        le=3.5,
        description="World Bank Worldwide Governance Indicators standardized political risk z-score (Flammer et al. 2024)"
    )
    project_sector: str = Field(
        default="renewable_infrastructure",
        description="Project sector: renewable_infrastructure, msme_credit_facilities, social_infrastructure"
    )
    mdb_capital_provisioning_rule: str = Field(
        default="one_to_one_aaa_constraint",
        description="MDB provisioning: one_to_one_aaa_constraint (caps guarantees at ~5% of commitments) or portfolio_risk_weighted"
    )


def simulate_blended_finance(inp: BlendedFinanceInput) -> Dict[str, Any]:
    """Calculate private capital mobilization (PCM), guarantee-induced risk compression, and geographic allocation skews."""
    total_capital = (
        inp.concessional_first_loss_grant_million_usd
        + inp.multilateral_subordinated_loan_million_usd
        + inp.target_commercial_senior_debt_million_usd
    )

    # Private capital mobilization leverage ratio: Private Commercial / Public Concessional
    public_de_risking_capital = inp.concessional_first_loss_grant_million_usd + inp.multilateral_subordinated_loan_million_usd
    private_mobilization_ratio = inp.target_commercial_senior_debt_million_usd / public_de_risking_capital if public_de_risking_capital > 0 else 0.0

    # Guarantee-Induced Risk Premium Compression (Matthäus & Mehling 2020; Aitkazin et al. 2026):
    # Guarantees compress risk premia by up to 22% in Sub-Saharan Africa and high-spread regions
    baseline_spread = inp.sovereign_credit_spread_bps
    if inp.enable_credit_guarantee_mechanism:
        # Compression scales with guarantee coverage ratio (up to 22% reduction in remuneration spread)
        spread_compression_factor = 0.22 * (inp.guarantee_coverage_ratio_percent / 100.0)
        effective_spread = baseline_spread * (1.0 - spread_compression_factor)
        guarantee_savings_percent = round(spread_compression_factor * 100.0, 1)
    else:
        effective_spread = baseline_spread
        guarantee_savings_percent = 0.0

    # Weighted Average Cost of Capital (WACC):
    w_grant = inp.concessional_first_loss_grant_million_usd / total_capital if total_capital > 0 else 0
    w_mdb = inp.multilateral_subordinated_loan_million_usd / total_capital if total_capital > 0 else 0
    w_private = inp.target_commercial_senior_debt_million_usd / total_capital if total_capital > 0 else 0

    cost_grant = 0.0
    cost_mdb = 2.5
    cost_private = 5.0 + (effective_spread / 100.0)
    unblended_cost_private = 5.0 + (baseline_spread / 100.0)
    blended_wacc = (w_grant * cost_grant) + (w_mdb * cost_mdb) + (w_private * cost_private)

    # Net Economic Margin: Economic IRR - Blended WACC
    economic_margin = inp.project_projected_economic_irr_percent - blended_wacc

    # Empirical Concessionality Scaling (Flammer et al. 2024):
    # Blended finance provides higher concessionality subsidies in contexts with high political risk (Z-score)
    concessionality_subsidy_share_percent = round(min(max(10.0 + (inp.country_political_risk_z_score * 8.5), 2.0), 45.0), 1)

    # Sector & Geographic Allocation Skew Matrix (Figure 2 Synthesis):
    allocation_skew_matrix = [
        {
            "sector_or_asset_class": "Renewable Infrastructure",
            "structural_mechanism": "Guarantees compress early-stage construction and offtake risks (B. 2026; McHugh 2021; Ayobami-Akanbi 2026)",
            "realized_allocation_impact": "Drives the largest volume of mobilized private capital globally (Aitkazin et al. 2026; Matthäus & Mehling 2020)"
        },
        {
            "sector_or_asset_class": "MSME Credit Facilities",
            "structural_mechanism": "Portfolio risk pooling and second-loss absorption across local intermediary banks (Nwani et al. 2022; Sharma et al. 2023)",
            "realized_allocation_impact": "Expands local working capital access but remains bottlenecked by domestic financial sector depth (Sharma et al. 2023)"
        },
        {
            "sector_or_asset_class": "Middle-Income Markets",
            "structural_mechanism": "Preference for creditworthy off-takers, established legal stability, and bankable project pipelines (Griffith-Jones et al. 2021)",
            "realized_allocation_impact": "Severe geographic concentration: absorbs disproportionate guarantee commitments away from highest-need LDCs (Bartenev 2025; Azar et al. 2026)"
        },
        {
            "sector_or_asset_class": "Frontier & Fragile States",
            "structural_mechanism": "Concessional subsidies scaled to extreme political opacity and off-taker risk (Flammer et al. 2024)",
            "realized_allocation_impact": "Faces persistent under-deployment due to full 1:1 capital provisioning rules and currency mismatches (Griffith-Jones et al. 2021; Hourcade et al. 2021)"
        }
    ]

    # Institutional Provisioning Constraint Evaluation (Hourcade et al. 2021; Santos & Kearney 2018):
    if inp.mdb_capital_provisioning_rule == "one_to_one_aaa_constraint":
        provisioning_status = "STRICT 1:1 CAPITAL PROVISIONING: MDB allocates dollar-for-dollar equity against guarantees to preserve AAA credit ratings, artificially constraining guarantee deployment to ~5% of commitments (Hourcade et al. 2021; Santos & Kearney 2018)."
    else:
        provisioning_status = "PORTFOLIO RISK-WEIGHTED PROVISIONING: Capital charges set actuarially across pooled diversified guarantee portfolios, expanding operational headroom by 3-4x."

    return {
        "engine": "Blended Finance Capital Stack & MDB Mobilization Engine",
        "domain": "development-finance",
        "project_total_capex_million_usd": inp.project_total_capex_million_usd,
        "private_capital_mobilization_ratio": f"1 : {round(private_mobilization_ratio, 2)}",
        "blended_weighted_average_cost_of_capital_percent": round(blended_wacc, 2),
        "unblended_commercial_borrowing_cost_percent": round(unblended_cost_private, 2),
        "guaranteed_commercial_cost_percent": round(cost_private, 2),
        "interest_cost_savings_spread_percent": round(unblended_cost_private - blended_wacc, 2),
        "net_economic_spread_margin_percent": round(economic_margin, 2),
        "guarantee_mechanism_evaluation": {
            "enabled": inp.enable_credit_guarantee_mechanism,
            "coverage_ratio_percent": inp.guarantee_coverage_ratio_percent,
            "remuneration_savings_induced_percent": guarantee_savings_percent,
            "political_risk_z_score": inp.country_political_risk_z_score,
            "flammer_concessionality_subsidy_percent": concessionality_subsidy_share_percent,
            "provisioning_constraint": provisioning_status,
            "contingent_liability_risk": "Off-budget guarantees risk unhedged sovereign contingent liabilities unless backed by explicit fiscal reserves (Griffith-Jones et al. 2021; Irwin 2007).",
            "currency_mismatch_warning": "Local currency revenue paired with hard-currency debt guarantees triggers structuring bottlenecks in frontier markets (Aitkazin et al. 2026; Muposhi 2026).",
            "allocation_skew_matrix": allocation_skew_matrix
        },
        "bankability_assessment": (
            "HIGHLY BANKABLE & COMMERCIALLY VIABLE: Subordinated first-loss tranche and guarantee compress borrowing cost below economic rate of return."
            if economic_margin > 3.0
            else "MARGINAL BANKABILITY: Requires additional concessional grant de-risking to attract private institutional capital."
        ),
        "framework_reference": "G20 Principles for Quality Infrastructure Investment, OECD Blended Finance Derisking Report (2025), & DFI Working Group Guidelines.",
        "literature_citations": [
            "Aitkazin, Z. et al. (2026). Blended finance and credit guarantees of IFIs. Bulletin, 10.32014/2026.2518-1467.1256",
            "Ayobami-Akanbi, F. (2026). De-Risking Renewable Energy Investments. Econova, 10.63084/econova.v3i1.113",
            "Azar, R. et al. (2026). Ratings and Blended Finance for Sustainable Development. Mediterr. J. Soc. Sci., 10.36941/mjss-2026-0097",
            "B., D. R. (2026). Structuring Project Finance for Energy Megaprojects. World J. Adv. Res. Rev., 10.30574/wjarr.2026.31.3.2382",
            "Bartenev, V. (2025). Guarantee Instruments in International Development Finance. Financ. J., 10.31107/2075-1990-2025-1-27-44",
            "Bau, N., & Dietrich, S. (2026). Guaranteeing the Global Gateway. J. Eur. Integr., 10.1080/07036337.2026.2720059",
            "Flammer, C. et al. (2024). Blended Finance. J. Financ. Econ., 10.3386/w32287",
            "Griffith-Jones, S. et al. (2021). Matching Risks with Instruments in Development Banks. Rev. Polit. Econ., 10.1080/09538259.2021.1978229",
            "Hourcade, J. et al. (2021). Accelerating speed and scale of climate finance. Clim. Policy, 10.1080/14693062.2021.1977599",
            "Irwin, T. C. (2007). Government Guarantees: Allocating and Valuing Risk. World Bank, 10.1596/978-0-8213-6858-9",
            "Matthäus, D., & Mehling, M. (2020). De-risking Renewable Energy Investments: Multilateral Guarantee Mechanism. Joule, 10.1016/j.joule.2020.10.011",
            "McHugh, C. A. (2021). Mobilising Private Funding of Development Finance. J. Dev. Stud., 10.1080/00220388.2021.1945042",
            "Muposhi, L. (2026). Structuring Blended Finance into African Infrastructure. SSRN, 10.2139/ssrn.6481678",
            "Musthaq, F. (2020). Development Finance or Financial Accumulation for Asset Managers?. New Polit. Econ., 10.1080/13563467.2020.1782367",
            "Nwani, S. et al. (2022). Integrating Credit Guarantee Schemes through Multi-Tier Risk-Sharing. IJSSER, 10.54660/ijsser.2022.1.2.125-130",
            "Prontera, A., & Quitzow, R. (2024). Development banks and politics of de-risking in European finance. Compet. Change, 10.1177/10245294241303803",
            "Santos, P. D. P., & Kearney, M. (2018). MDBs Risk Mitigation Instruments for Infrastructure. IDB, 10.18235/0001008",
            "Sharma, K. et al. (2023). Bibliometric Review of Blended Finance and Partial Risk Guarantee. Int. J. Financ. Stud., 10.3390/ijfs11030103"
        ]
    }
