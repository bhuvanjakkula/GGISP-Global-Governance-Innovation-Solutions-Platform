"""Specialist Engine 11: OECD Pillar Two GloBE Global Minimum Tax & Transparency Framework Simulator.
Reference: OECD/G20 BEPS 2.0 / Country-by-Country Reporting (CbCR) / Real Investment Spillovers.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class InternationalTaxInput(BaseModel):
    jurisdiction_code: str = Field(default="KEN", min_length=2, max_length=5)
    in_scope_mne_global_revenue_euro_million: float = Field(default=850.0, ge=750.0, description="In-scope threshold is >= 750M EUR")
    local_constituent_entity_profit_million_usd: float = Field(default=120.0, ge=1.0, le=50000.0)
    covered_taxes_paid_million_usd: float = Field(default=10.8, ge=0.0, le=20000.0)
    substance_based_income_exclusion_payroll_percent: float = Field(default=9.6, ge=5.0, le=10.0, description="Payroll carve-out %")
    local_payroll_cost_million_usd: float = Field(default=18.0, ge=0.0, le=5000.0)
    tangible_assets_million_usd: float = Field(default=35.0, ge=0.0, le=10000.0)
    substance_based_income_exclusion_assets_percent: float = Field(default=7.6, ge=5.0, le=8.0, description="Tangible assets carve-out %")
    global_minimum_tax_rate_percent: float = Field(default=15.0)

    # Tax Transparency Frameworks & Real Investment Reallocation (Choi et al. 2020; De Vito et al. 2025; Feng et al. 2026)
    transparency_disclosure_regime: str = Field(
        default="mandatory_cbcr_and_aeoi",
        description="Transparency regime: mandatory_cbcr_and_aeoi, public_cbcr_disclosed, opaque_secrecy_baseline"
    )
    tax_competition_pivot_strategy: str = Field(
        default="regulatory_structural_incentives",
        description="Host nation competitive strategy: statutory_rate_race_to_bottom, regulatory_structural_incentives, accounting_standard_divergence"
    )
    foreign_parent_tax_hike_intensity_percent: float = Field(
        default=4.5,
        ge=0.0,
        le=30.0,
        description="Corporate tax hike intensity in multinational parent/linked country % (De Vito et al. 2025)"
    )
    mne_segment_disclosure_aggregation: bool = Field(
        default=True,
        description="MNE aggregates geographical segment reporting to obscure sensitive affiliate transactions (Akamah et al. 2017)"
    )


def simulate_international_tax(inp: InternationalTaxInput) -> Dict[str, Any]:
    """Calculate Effective Tax Rate (ETR), Top-Up Tax, and Real MNE Investment Reallocations under Transparency Regimes."""
    profit = inp.local_constituent_entity_profit_million_usd
    covered_taxes = inp.covered_taxes_paid_million_usd

    # Effective Tax Rate: ETR = Covered Taxes / GloBE Income
    etr = (covered_taxes / profit) * 100.0 if profit > 0 else 0.0

    # Top-up tax percentage: Top-up % = max(15% - ETR, 0%)
    top_up_percentage = max(inp.global_minimum_tax_rate_percent - etr, 0.0)

    # Substance-based income exclusion (SBIE):
    payroll_carveout = inp.local_payroll_cost_million_usd * (inp.substance_based_income_exclusion_payroll_percent / 100.0)
    assets_carveout = inp.tangible_assets_million_usd * (inp.substance_based_income_exclusion_assets_percent / 100.0)
    total_sbie = payroll_carveout + assets_carveout

    # Excess profit subject to top-up tax:
    excess_profit = max(profit - total_sbie, 0.0)
    jurisdictional_top_up_tax_million = excess_profit * (top_up_percentage / 100.0)

    # Transparency Framework & Profit-Shifting Deterrence Modeling (Feng et al. 2026; Müller et al. 2020; He et al. 2024):
    transparency_mode = inp.transparency_disclosure_regime.lower().strip()
    if transparency_mode == "public_cbcr_disclosed":
        detection_prob_percent = 92.0
        profit_shifting_deterrence_percent = 48.0
        financial_channel_substitution_percent = 38.0
        disclosure_finding = "HIGH TRANSPARENCY: Public CbCR sharply curtails artificial conduit entities but induces substitution toward internal debt and hybrid instruments (He et al. 2024; Joshi et al. 2020)."
    elif transparency_mode == "mandatory_cbcr_and_aeoi":
        detection_prob_percent = 78.0
        profit_shifting_deterrence_percent = 35.0
        financial_channel_substitution_percent = 26.0
        disclosure_finding = "CONFIDENTIAL MULTILATERAL CbCR: Information exchanges raise audit detectability; tax authorities gain visibility while firms preserve commercial secrecy (Feng et al. 2026; Müller et al. 2020)."
    else:
        detection_prob_percent = 22.0
        profit_shifting_deterrence_percent = 5.0
        financial_channel_substitution_percent = 8.0
        disclosure_finding = "OPAQUE SECRECY BASELINE: Low audit visibility enables unconstrained conduit routing and aggressive IP profit shifting (Choi et al. 2020)."

    # Real Multinational Investment Spillover Elasticity (De Vito et al. 2025; Bares et al. 2026):
    # Production linkage effect: A 1pp parent tax hike reduces subsidiary investment by ~0.35% due to higher cross-border capital costs
    subsidiary_investment_spillover_percent = -round(inp.foreign_parent_tax_hike_intensity_percent * 0.35, 2)

    # Reallocation of Multinational Investment Dimensions Matrix (Figure 2 Synthesis):
    investment_reallocation_matrix = [
        {
            "dimension": "Tax Haven Allocations",
            "behavioral_mechanism": "Diminishing secrecy premiums and elevated audit detection risks (Feng et al. 2026; Temouri et al. 2021; Tardios & Clegg 2024)",
            "empirical_finding": "Decreased capital deployment to low-tax jurisdictions and reduced conduit routing (Müller et al. 2020; He et al. 2024)"
        },
        {
            "dimension": "Intangible Property (IP) Placement",
            "behavioral_mechanism": "Realignment of legal rights with verifiable economic substance and R&D staffing (Judijanto et al. 2025; Dischinger & Riedel 2011)",
            "empirical_finding": "High tax elasticity remains, but firms substitute scrutinized patent boxes with financial and intercompany debt channels (Temouri et al. 2021; He et al. 2024)"
        },
        {
            "dimension": "Cross-Border Acquisitions",
            "behavioral_mechanism": "Reduced availability of Outbound Profit Shifting (OPS) reduces net acquisition returns (Tardios & Clegg 2024)",
            "empirical_finding": "Lower acquisition propensity in transparent host markets lacking bilateral secrecy protections (Shen 2023; Tardios & Clegg 2024)"
        },
        {
            "dimension": "Downstream Subsidiary Capital",
            "behavioral_mechanism": "Production linkages and global minimum tax capital cost inflation (Bares et al. 2026; De Vito et al. 2025)",
            "empirical_finding": f"Negative spillovers reduce real affiliate capex by {abs(subsidiary_investment_spillover_percent)}% as corporate networks internalize foreign tax hikes (De Vito et al. 2025)"
        }
    ]

    # Tax Competition Dynamics & Game-Theoretic Pivot (Choi et al. 2020; Balza 2025; Diller et al. 2024):
    strat = inp.tax_competition_pivot_strategy.lower().strip()
    if strat == "regulatory_structural_incentives":
        competition_posture = "SMART REGULATION & LEGAL STABILITY: Jurisdiction pivots to streamlined administrative permitting, skilled labor subsidies, and stable property rights to retain FDI without cutting tax rates (Balza 2025; Ama & Yanney 2025)."
    elif strat == "accounting_standard_divergence":
        competition_posture = "UNHARMONIZED ACCOUNTING STANDARDS: Distortions persist as national differences in book-tax accounting rules undermine collective minimum tax baselines (Diller et al. 2024)."
    else:
        competition_posture = "STATUTORY RATE RACE TO THE BOTTOM: Unilateral rate slashing accelerated by low mutual audit oversight (Choi et al. 2020; Shen 2023)."

    return {
        "engine": "OECD Pillar Two GloBE Global Minimum Tax & Transparency Simulator",
        "domain": "international-tax",
        "jurisdiction": inp.jurisdiction_code,
        "effective_tax_rate_etr_percent": round(etr, 2),
        "statutory_minimum_tax_threshold_percent": inp.global_minimum_tax_rate_percent,
        "top_up_tax_rate_gap_percent": round(top_up_percentage, 2),
        "substance_based_income_exclusion_million_usd": round(total_sbie, 2),
        "excess_profit_taxable_base_million_usd": round(excess_profit, 2),
        "projected_top_up_tax_revenue_million_usd": round(jurisdictional_top_up_tax_million, 2),
        "pillar_two_compliance_status": (
            "TAX HAVEN / LOW-TAX EXPOSURE: Top-up tax applies via Qualified Domestic Minimum Top-up Tax (QDMTT) or Income Inclusion Rule (IIR)."
            if top_up_percentage > 0.0
            else "COMPLIANT JURISDICTION: ETR meets or exceeds the 15% international minimum standard."
        ),
        "tax_transparency_framework_evaluation": {
            "regime": inp.transparency_disclosure_regime,
            "audit_detection_probability_percent": detection_prob_percent,
            "profit_shifting_deterrence_rate_percent": profit_shifting_deterrence_percent,
            "financial_channel_substitution_rate_percent": financial_channel_substitution_percent,
            "disclosure_assessment": disclosure_finding,
            "tax_competition_dynamic": competition_posture,
            "mne_investment_reallocation_matrix": investment_reallocation_matrix,
            "subsidiary_investment_spillover_percent": subsidiary_investment_spillover_percent,
            "strategic_reporting_aggregations": (
                "MNE employs geographic segment aggregation to obscure sensitive intra-group margins (Akamah et al. 2017), reducing peer firm investment efficiency (Nessa et al. 2026)."
                if inp.mne_segment_disclosure_aggregation
                else "Disaggregated segment reporting provides transparent jurisdictional transfer pricing visibility."
            ),
            "developing_country_capacity_warning": "Administrative asymmetries between advanced and developing authorities persist, restricting substantive enforcement of CbCR data in low-capacity nations (Judijanto et al. 2025)."
        },
        "international_architecture": "OECD/G20 Base Erosion and Profit Shifting (BEPS) 2.0 Two-Pillar Solution & Multilateral Competent Authority Agreement (MCAA).",
        "literature_citations": [
            "Akamah, H. T. et al. (2017). Tax havens and disclosure aggregation. J. Int. Bus. Stud., 10.1057/s41267-017-0084-x",
            "Balza, B. (2025). Role of Tax Law in Attracting FDI. sj-economics, 10.58246/sj-economics.v57i2.676",
            "Bares, F. et al. (2026). Impact of global minimum tax on location, investment, and profit shifting. J. Int. Bus. Stud., 10.1057/s41267-026-00860-z",
            "Choi, J. et al. (2020). Transfer pricing regulation and tax competition. J. Int. Econ., 10.1016/j.jinteco.2020.103367",
            "De Vito, A. et al. (2025). How do corporate tax hikes affect investment allocation within multinationals?. Rev. Finance, 10.1093/rof/rfaf006",
            "Diller, M. et al. (2024). Is Tax Transfer Pricing Harmonization a Panacea?. Account. Rev., 10.2308/tar-2021-0477",
            "Dischinger, M., & Riedel, N. (2011). Corporate taxes and the location of intangible assets. J. Public Econ., 10.1016/j.jpubeco.2010.12.002",
            "Feng, J. et al. (2026). Evidence from Chinese Multinational Firms. Emerg. Mark. Finance Trade, 10.1080/1540496x.2026.2679045",
            "He, B. et al. (2024). Information Transparency and International Tax Avoidance Channels. Open Econ. Rev., 10.1007/s11079-024-09790-5",
            "Joshi, P. et al. (2020). Does Public CbCR Deter Tax Avoidance?. Contemp. Account. Res., 10.1111/1911-3846.12601",
            "Judijanto, L. et al. (2025). Global Tax Transparency and Fairness. J. Markcount Finance, 10.70177/jmf.v3i3.2927",
            "Müller, R. et al. (2020). Determinants and Effects of Corporate Tax Transparency. SSRN, 10.2139/ssrn.3736747",
            "Nessa, M. L. et al. (2026). Market Leaders’ Tax-Motivated Income Shifting and Investment Efficiency. Account. Rev., 10.2308/tar-2024-0328",
            "Tardios, J. A., & Clegg, L. (2024). Outbound Profit Shifting and Cross-Border Acquisitions. Br. J. Manage., 10.1111/1467-8551.12825",
            "Temouri, Y. et al. (2021). Tax havens and international business: accountability-avoiding FDI. Int. J. Manage. Rev., 10.1111/ijmr.12279"
        ]
    }
