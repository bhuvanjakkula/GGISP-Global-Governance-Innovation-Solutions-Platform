"""Central Registry for all 13 Specialist Quantitative Policy Innovation Engines."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

from ggisp.specialist_engines.ai_frontier_governance import AIGovernanceInput, simulate_ai_frontier_governance
from ggisp.specialist_engines.climate_parametric_loss import ClimateParametricInput, simulate_climate_parametric
from ggisp.specialist_engines.critical_minerals_hhi import CriticalMineralsInput, simulate_critical_minerals
from ggisp.specialist_engines.cyber_defensive_matrix import CyberDefenseInput, simulate_cyber_defense
from ggisp.specialist_engines.development_finance_stack import BlendedFinanceInput, simulate_blended_finance
from ggisp.specialist_engines.global_health_surveillance import GlobalHealthInput, simulate_global_health
from ggisp.specialist_engines.international_tax_globe import InternationalTaxInput, simulate_international_tax
from ggisp.specialist_engines.nuclear_safeguards import NuclearSafeguardsInput, simulate_nuclear_safeguards
from ggisp.specialist_engines.ocean_marine_depletion import OceanGovernanceInput, simulate_ocean_governance
from ggisp.specialist_engines.sovereign_debt_stochastic import StochasticDSAInput, simulate_stochastic_dsa
from ggisp.specialist_engines.space_orbital_debris import SpaceDebrisInput, simulate_space_debris
from ggisp.specialist_engines.un_veto_dynamics import UNSCVotingInput, simulate_unsc_voting
from ggisp.specialist_engines.wto_gravity_trade import GravityTradeInput, simulate_gravity_trade

ENGINE_CATALOG: Dict[str, Dict[str, Any]] = {
    "nuclear-security": {
        "engine_name": "Nuclear Safeguards & Breakout Estimator",
        "domain_slug": "nuclear-security",
        "reference_institution": "IAEA / UN-ODA",
        "input_class": NuclearSafeguardsInput,
        "handler": simulate_nuclear_safeguards,
        "description": "Calculates Separative Work Units (SWU), material accountancy balance, and weaponization breakout timelines under IAEA verification standards.",
    },
    "un-security-council": {
        "engine_name": "UNSC Veto Dynamics & Coalition Engine",
        "domain_slug": "un-security-council",
        "reference_institution": "UN General Assembly / UN Charter Ch. VII",
        "input_class": UNSCVotingInput,
        "handler": simulate_unsc_voting,
        "description": "Calculates P5 veto risk probabilities, Shapley-Shubik voting power distribution, and General Assembly Resolution 377A referral likelihood.",
    },
    "wto-trade": {
        "engine_name": "Structural Gravity Trade & Chokepoint Engine",
        "domain_slug": "wto-trade",
        "reference_institution": "WTO / UNCTAD",
        "input_class": GravityTradeInput,
        "handler": simulate_gravity_trade,
        "description": "Predicts bilateral trade flows using structural gravity coefficients, tariff escalation sensitivities, and maritime chokepoint transit risks.",
    },
    "sovereign-debt": {
        "engine_name": "Stochastic Sovereign DSA Fan Chart & Haircut Engine",
        "domain_slug": "sovereign-debt",
        "reference_institution": "IMF / World Bank / Paris Club",
        "input_class": StochasticDSAInput,
        "handler": simulate_stochastic_dsa,
        "description": "Simulates 1,000 Monte Carlo stochastic debt trajectories to generate 10th-90th percentile fan charts and compute NPV debt relief targets.",
    },
    "ai-governance": {
        "engine_name": "Frontier AI Compute & Dual-Use Risk Registry",
        "domain_slug": "ai-governance",
        "reference_institution": "NIST AI RMF / OECD AI Principles / ITU",
        "input_class": AIGovernanceInput,
        "handler": simulate_ai_frontier_governance,
        "description": "Calculates cumulative FLOPs, checks 10^26 frontier covenant thresholds, hardware cluster auditing, and dual-use biosecurity benchmarks.",
    },
    "cybersecurity": {
        "engine_name": "Defensive Cyber Resilience & PQC Migration Matrix",
        "domain_slug": "cybersecurity",
        "reference_institution": "ITU / UN OEWG / NIST FIPS 203",
        "input_class": CyberDefenseInput,
        "handler": simulate_cyber_defense,
        "description": "Evaluates critical infrastructure defensive coverage, CSIRT incident latency, and Mosca's Theorem for post-quantum cryptographic migration.",
    },
    "global-health": {
        "engine_name": "Epidemiological SEIR Early-Warning & Vaccine Surge Allocator",
        "domain_slug": "global-health",
        "reference_institution": "WHO / CEPI / IHR 2005",
        "input_class": GlobalHealthInput,
        "handler": simulate_global_health,
        "description": "Projects pathogen transmission curves with variant immune evasion parameters, ICU bed demand, and equitable vaccine surge allocations.",
    },
    "space-security": {
        "engine_name": "LEO Orbital Debris Conjunction & Space Traffic Engine",
        "domain_slug": "space-security",
        "reference_institution": "UN COPUOS / IADC",
        "input_class": SpaceDebrisInput,
        "handler": simulate_space_debris,
        "description": "Calculates orbital collision probabilities (Pc), conjunction miss distances, and 5-year post-mission satellite deorbit compliance.",
    },
    "critical-minerals": {
        "engine_name": "Critical Minerals Supply Concentration & Circularity Engine",
        "domain_slug": "critical-minerals",
        "reference_institution": "IEA / Minerals Security Partnership",
        "input_class": CriticalMineralsInput,
        "handler": simulate_critical_minerals,
        "description": "Calculates Herfindahl-Hirschman Indices (HHI) for battery minerals, evaluates export embargo deficits, and closed-loop recycling offsets.",
    },
    "ocean-governance": {
        "engine_name": "High Seas Marine Biodiversity & BBNJ Harvest Engine",
        "domain_slug": "ocean-governance",
        "reference_institution": "UN BBNJ Treaty / UNCLOS / FAO",
        "input_class": OceanGovernanceInput,
        "handler": simulate_ocean_governance,
        "description": "Models Schaefer biomass replenishment, Maximum Sustainable Yield (MSY), illegal IUU extraction pressure, and 30x30 MPA spillovers.",
    },
    "international-tax": {
        "engine_name": "OECD Pillar Two GloBE 15% Minimum Tax Simulator",
        "domain_slug": "international-tax",
        "reference_institution": "OECD/G20 Inclusive Framework on BEPS",
        "input_class": InternationalTaxInput,
        "handler": simulate_international_tax,
        "description": "Calculates Effective Tax Rates (ETR), substance-based payroll/asset carve-outs, and top-up tax revenue under QDMTT and IIR rules.",
    },
    "development-finance": {
        "engine_name": "Blended Finance Capital Stack & MDB Mobilization Engine",
        "domain_slug": "development-finance",
        "reference_institution": "OECD Blended Finance / DFI Working Group",
        "input_class": BlendedFinanceInput,
        "handler": simulate_blended_finance,
        "description": "Optimizes junior first-loss concessional tranches, computes private capital mobilization (PCM) ratios, and blended cost of capital (WACC).",
    },
    "climate-finance": {
        "engine_name": "Loss & Damage Parametric Trigger & Article 6 Carbon Engine",
        "domain_slug": "climate-finance",
        "reference_institution": "UNFCCC COP28 Loss & Damage Fund / Paris Art. 6",
        "input_class": ClimateParametricInput,
        "handler": simulate_climate_parametric,
        "description": "Evaluates parametric catastrophe triggers for rapid disaster liquidity payouts and calculates Article 6.2/6.4 sovereign carbon revenues.",
    },
}


def list_specialist_engines() -> List[Dict[str, Any]]:
    """Return catalog of all 13 quantitative engines with their default schemas."""
    res = []
    for slug, meta in ENGINE_CATALOG.items():
        sample_input = meta["input_class"]().model_dump()
        res.append({
            "domain_slug": slug,
            "engine_name": meta["engine_name"],
            "reference_institution": meta["reference_institution"],
            "description": meta["description"],
            "default_parameters": sample_input,
        })
    return res


def execute_specialist_engine(domain_slug: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the domain-specific specialist engine."""
    slug = domain_slug.strip().lower()
    if slug not in ENGINE_CATALOG:
        raise ValueError(f"No specialist engine found for domain: '{slug}'")

    meta = ENGINE_CATALOG[slug]
    input_obj = meta["input_class"](**parameters)
    return meta["handler"](input_obj)
