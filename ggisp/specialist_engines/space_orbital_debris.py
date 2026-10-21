"""Specialist Engine 8: LEO Orbital Debris Conjunction Probability, Space Security, & Spaceport State Control (SpSC) Engine.
Reference: UN COPUOS (68th Session) / IADC / UNCLOS Art. 218-219 / 1967 Outer Space Treaty / 1972 Liability Convention.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class SpaceDebrisInput(BaseModel):
    satellite_altitude_km: float = Field(default=550.0, ge=300.0, le=2000.0, description="Orbital perigee altitude in km")
    satellite_cross_section_m2: float = Field(default=15.0, ge=0.1, le=500.0)
    conjunction_miss_distance_meters: float = Field(default=120.0, ge=1.0, le=50000.0)
    relative_encounter_velocity_km_s: float = Field(default=10.5, ge=1.0, le=16.0)
    maneuver_propulsion_delta_v_m_s: float = Field(default=25.0, ge=0.0, le=200.0)
    debris_density_objects_per_km3: float = Field(default=1.8e-8, ge=1e-10, le=1e-6)
    post_mission_deorbit_planned_years: int = Field(default=4, ge=1, le=50)

    # Advanced Space Security & Orbital Governance (Tiwari et al. 2024; Semenov 2026; Popova 2025; Klimburg-Witjes et al. 2025)
    debris_size_band: str = Field(
        default="greater_than_1cm",
        description="Debris size class: greater_than_10cm (tracked), greater_than_1cm (lethal unshielded), less_than_1cm (micrometeoroids)"
    )
    space_situational_awareness_catalog: str = Field(
        default="open_multilateral_catalog",
        description="SSA tracking regime: open_multilateral_catalog (transparent) or classified_national_catalog (siloed secrecy)"
    )
    threat_dimension: str = Field(
        default="constellation_congestion",
        description="Threat vector: kinetic_asat_testing, constellation_congestion, non_kinetic_interference, nuclear_power_sources"
    )
    active_debris_removal_protocol: str = Field(
        default="registered_state_bilateral_consent",
        description="ADR legal authorization: registered_state_bilateral_consent, unilateral_salvage_unauthorized"
    )

    # Spaceport State Control (SpSC) & Economic Mechanisms (Abuelenin 2025; Bennett 2025; Janikowski 2026)
    enable_spaceport_state_control: bool = Field(
        default=True,
        description="Maritime Port State Control analog conditioning launch access on verified mitigation compliance (Abuelenin 2025)"
    )
    spaceport_jurisdiction_mou_network: bool = Field(
        default=True,
        description="Regional Memoranda of Understanding across spaceports preventing regulatory arbitrage (Pietrzak 2026; Jain & Rao 2022)"
    )
    remediation_bond_deposit_secured: bool = Field(
        default=True,
        description="Financial remediation bond deposited if satellite design exceeds baseline deorbit horizons"
    )
    orbital_use_fee_per_kg_usd: float = Field(
        default=150.0,
        ge=0.0,
        le=5000.0,
        description="Pigouvian orbital use fee internalizing orbital congestion externalities (Bennett 2025; Morin & Richard 2021)"
    )
    liability_standard_regime: str = Field(
        default="strict_environmental_fault_inversion",
        description="Liability regime: fault_based_liability_status_quo, strict_environmental_fault_inversion, cbdr_polluter_pays"
    )


def simulate_space_debris(inp: SpaceDebrisInput) -> Dict[str, Any]:
    """Calculate conjunction collision probability, SSA tracking fidelity, and Spaceport State Control compliance."""
    # Positional covariance uncertainty sigma:
    # Classified siloed catalogs expand uncertainty due to latency and data withholding (Klimburg-Witjes et al. 2025)
    if inp.space_situational_awareness_catalog == "classified_national_catalog":
        sigma = 115.0  # meters
        ssa_tracking_efficiency = "DEGRADED: National secrecy and classified catalogs withhold critical orbital ephemeris data (Klimburg-Witjes et al. 2025)."
    else:
        sigma = 42.0  # meters
        ssa_tracking_efficiency = "OPTIMAL: Open multilateral SSA tracking achieves narrow positional covariance margins."

    # Foster's 2D Gaussian probability of collision:
    # Combined collision radius R = r_sat + r_debris ~= sqrt(A_sat / pi) + 0.5m
    r_comb = math.sqrt(inp.satellite_cross_section_m2 / math.pi) + 0.5
    d = inp.conjunction_miss_distance_meters

    # Collision probability integral approximation: P_c = (R^2 / (2 * sigma^2)) * exp(-d^2 / (2 * sigma^2))
    p_c = (r_comb ** 2 / (2.0 * sigma ** 2)) * math.exp(-(d ** 2) / (2.0 * sigma ** 2))
    p_c = min(p_c, 1.0)

    # Threshold for Collision Avoidance Maneuver (CAM): NASA / ESA standard threshold is 1e-4
    maneuver_mandatory = p_c >= 1e-4

    # Post-mission disposal compliance: 2022 FCC/IADC rule mandates deorbit within 5 years (Bennett 2025)
    iadc_compliant = inp.post_mission_deorbit_planned_years <= 5

    # Spaceport State Control (SpSC) Decision Tree Execution (Abuelenin 2025; Janikowski 2026; Pietrzak 2026):
    if not inp.enable_spaceport_state_control:
        spsc_status = "INACTIVE: Unilateral flag-state licensing permits flags of convenience and regulatory leakage (Mejía-Kaiser 2020)."
        orbital_access_granted = True
    elif iadc_compliant:
        spsc_status = "LAUNCH AUTHORIZATION GRANTED: Satellite verified compliant with IADC 5-year post-mission disposal standards (Abuelenin 2025)."
        orbital_access_granted = True
    elif inp.remediation_bond_deposit_secured:
        spsc_status = "CONDITIONAL LAUNCH AUTHORIZATION GRANTED: Non-compliant deorbit design offset by secured Remediation Escrow Bond & ADR clearinghouse contract (Janikowski 2026)."
        orbital_access_granted = True
    else:
        spsc_status = "ORBITAL ACCESS DENIED: Spaceport State Control refused liftoff and ground-station downlinking due to unbonded orbital hazard (Abuelenin 2025)."
        orbital_access_granted = False

    # Threat Dimension Operational Evaluation (Hordeiuk 2026; Maharani et al. 2025; Bennett 2025; Polkowska 2023):
    td = inp.threat_dimension.lower().strip()
    if td == "kinetic_asat_testing":
        threat_profile = {
            "threat_dimension": "Kinetic Anti-Satellite (ASAT) Missile Testing",
            "primary_operational_risk": "High-velocity hypervelocity fragmentation plumes expanding across orbital shells (Tiwari et al. 2024; Klimburg-Witjes et al. 2025).",
            "policy_or_mitigation_approach": "Multilateral destructive test moratoria and weaponization limits (Hordeiuk 2026; Maharani et al. 2025).",
            "legal_status": "Article IV OST covers only WMDs, leaving conventional kinetic ASAT weapons legally unprohibited."
        }
    elif td == "non_kinetic_interference":
        threat_profile = {
            "threat_dimension": "Non-Kinetic Electronic & Cyber Interference",
            "primary_operational_risk": "Disrupted telecommunications, spoofed telemetry, and uplink jamming (Polkowska 2023; Kostenko 2023).",
            "policy_or_mitigation_approach": "ITU Radio Regulations compliance, frequency coordination, and space cybersecurity standards (Johnson & Masson-Zwaan 2023; Maharani et al. 2025).",
            "legal_status": "Governed by ITU Constitution and customary non-harmful interference principles."
        }
    elif td == "nuclear_power_sources":
        threat_profile = {
            "threat_dimension": "Nuclear Power Sources (NPS) in Space",
            "primary_operational_risk": "Hazardous radiological orbital collisions dispersing fissile material into lower orbits or terrestrial atmosphere.",
            "policy_or_mitigation_approach": "Specialized UN NPS Principles reporting protocols, high-altitude graveyard storage orbits, and containment shielding.",
            "legal_status": "UN GA Resolution 47/68 (Principles Relevant to the Use of Nuclear Power Sources in Outer Space)."
        }
    else:  # constellation_congestion
        threat_profile = {
            "threat_dimension": "Mega-Constellation Congestion & Cascading Collisions",
            "primary_operational_risk": "Runaway collisional chain reactions rendering orbital bands unusable via Kessler syndrome (Migaud 2020; Runnels 2023).",
            "policy_or_mitigation_approach": "Satellite lifecycle disposal rules, launch license capacity caps, and active collision avoidance maneuvers (Bennett 2025).",
            "legal_status": "Voluntary COPUOS Long-term Sustainability (LTS) Guidelines; FCC 5-year post-mission rule."
        }

    # Space Law and Peaceful-Use Governance Assessment (Popova 2025; Semenov 2026; Handmer & Freeland 2022):
    adr_status = inp.active_debris_removal_protocol.lower().strip()
    if adr_status == "registered_state_bilateral_consent":
        adr_legality = "COMPLIANT: Launch state of registration provided formal authorization under Outer Space Treaty Article VIII."
    else:
        adr_legality = (
            "LEGAL VIOLATION / HIGH DISPUTE RISK: Derelict debris retains perpetual jurisdiction of the registry state "
            "under Article VIII of the 1967 Outer Space Treaty; unauthorized removal constitutes unlawful seizure (Popova 2025)."
        )

    # Operationalization Pathway & Liability Allocation (M 2026; Abuelenin 2025; Li 2015; Newman & Cheney 2023; Seffinga 2024):
    liab_regime = inp.liability_standard_regime.lower().strip()
    if liab_regime == "strict_environmental_fault_inversion":
        liability_eval = {
            "regime": "Strict Environmental Liability & Inverted Burden of Proof",
            "fault_standard": "Rebuttable presumption of fault: non-compliance with IADC mitigation benchmarks constitutes prima facie evidence of breach of care (Li 2015; Newman & Cheney 2023).",
            "enforcement_mechanism": "Arbitration under specialized PCA Optional Rules for Outer Space Disputes (Buszman 2023; Hosseini et al. 2021)."
        }
    elif liab_regime == "cbdr_polluter_pays":
        liability_eval = {
            "regime": "Common But Differentiated Responsibilities (CBDR) & Polluter-Pays Principle",
            "fault_standard": "Remediation and debris cleanup levies allocated proportionally to historical orbital utilization (M 2026; Svárovská 2021).",
            "enforcement_mechanism": "Multilateral Global Debris Removal Fund managed under UN COPUOS auspices (Sheer et al. 2023)."
        }
    else:
        liability_eval = {
            "regime": "1972 Liability Convention Article III Fault-Based Status Quo",
            "fault_standard": "Claimant must prove negligence on-orbit; virtually impossible for untracked millimeter and centimeter debris (M 2026; Seffinga 2024).",
            "enforcement_mechanism": "Posterior diplomatic Claims Commission without prior deterrence or anterior risk management (Gracin et al. 2025)."
        }

    # Comparative Governance Structure: Maritime PSC vs Spaceport State Control (Abuelenin 2025):
    comparative_governance_matrix = [
        {"parameter": "Jurisdictional Basis", "maritime_psc": "Coastal territorial sovereignty over internal waters (UNCLOS Art 218/219)", "spaceport_state_control": "Territorial sovereignty over launch and ground facilities (Abuelenin 2025)"},
        {"parameter": "Primary Target", "maritime_psc": "Substandard vessels and marine pollution (Napper et al. 2025)", "spaceport_state_control": "Non-compliant satellite designs and derelict orbital debris (Popova & Schaus 2018)"},
        {"parameter": "Enforcement Point", "maritime_psc": "Physical dockside inspection and vessel detention", "spaceport_state_control": "Pre-launch screening, ground-station downlinking licenses (Bennett 2025)"},
        {"parameter": "Multilateral Tool", "maritime_psc": "Regional Memoranda of Understanding (e.g. Paris MoU)", "spaceport_state_control": "Harmonized spaceport MoUs & treaty clearinghouses (Jain & Rao 2022)"},
        {"parameter": "Legal Limitation", "maritime_psc": "Freedom of navigation on high seas", "spaceport_state_control": "Perpetual registry jurisdiction & salvage bans (OST Art VIII; Nomura et al. 2024)"}
    ]

    operationalization_pathway = {
        "sequence": "Standards Codification -> Pre-Launch Licensing -> Remediation Framework -> Liability Allocation",
        "pre_launch_licensing": spsc_status,
        "orbital_access_decision": "GRANTED" if orbital_access_granted else "DENIED",
        "spaceport_arbitrage_prevention": (
            "Regional Spaceport MoU Network active: Uniform conditionality stops launch migration across jurisdictions (Pietrzak 2026)."
            if inp.spaceport_jurisdiction_mou_network
            else "High risk of regulatory arbitrage: Operators migrate payloads to permissive foreign launch facilities (Jain & Rao 2022)."
        ),
        "remediation_framework": {
            "jurisdiction_barrier_resolution": "Bilateral transfer-of-jurisdiction pacts under OST Article VIII (Long & Huang 2024; Haroun et al. 2021).",
            "salvage_rights": "Codified distinction between active satellites and derelict debris in Registration Convention (Haroun et al. 2021).",
            "liability_waivers": "Cross-waivers of liability and mutual indemnification pacts for active removal tugs under Liability Convention Article III (Long & Huang 2024).",
            "cleanup_financing": f"Dedicated Global Debris Removal Fund capitalizing public-private removal missions; orbital-use fee applied at ${inp.orbital_use_fee_per_kg_usd}/kg (Sheer et al. 2023; Bennett 2025)."
        },
        "liability_allocation": liability_eval,
        "comparative_maritime_matrix": comparative_governance_matrix
    }

    return {
        "engine": "LEO Orbital Debris Conjunction, Space Security & Spaceport State Control Engine",
        "domain": "space-security",
        "orbital_altitude_km": inp.satellite_altitude_km,
        "conjunction_miss_distance_meters": inp.conjunction_miss_distance_meters,
        "collision_probability_p_c": f"{p_c:.3e}",
        "collision_avoidance_maneuver_required": maneuver_mandatory,
        "iadc_5_year_post_mission_deorbit_compliance": iadc_compliant,
        "debris_catalog_context": {
            "tracked_objects_greater_than_1cm": ">500,000 hazardous fragments in low Earth orbit (Tiwari et al. 2024)",
            "selected_size_band": inp.debris_size_band,
            "ssa_tracking_posture": inp.space_situational_awareness_catalog,
            "tracking_fidelity": ssa_tracking_efficiency
        },
        "satellite_safety_challenge": threat_profile,
        "international_space_law_evaluation": {
            "outer_space_treaty_1967": "Binds signatories to explore and utilize outer space peacefully and for the benefit of all mankind (Tiwari et al. 2024; Runnels 2023).",
            "article_iv_regulatory_void": "Article IV of Outer Space Treaty restricts only weapons of mass destruction (WMD), leaving conventional kinetic ASAT weapons and orbital jamming unregulated (Hordeiuk 2026; Maharani et al. 2025).",
            "article_viii_property_hurdle": "Perpetual jurisdiction over registered space objects impedes Active Debris Removal (ADR) without prior consent (Popova 2025).",
            "active_debris_removal_authorization": adr_legality,
            "soft_law_evolution": "COPUOS 68th Session demonstrates progressive codification of voluntary technical guidelines into binding national licensing requirements (Semenov 2026; Handmer & Freeland 2022)."
        },
        "spaceport_state_control_system": operationalization_pathway,
        "traffic_coordination_status": (
            "CRITICAL CONJUNCTION RISK: Immediate collision avoidance maneuver (CAM) execution recommended."
            if maneuver_mandatory
            else "SAFE NOMINAL SEPARATION: Positional covariance within tolerable international safety margins."
        ),
        "literature_citations": [
            "Abuelenin, A. (2025). Port state control and sustainability of space: maritime enforcement paradigm. Discover Space, 10.1007/s11038-025-09579-7",
            "Bennett, M. M. (2025). Orbital debris requires prevention and mitigation across satellite life cycle. Commun. Eng., 10.1038/s44172-025-00430-5",
            "Buszman, Z. (2023). Sustainability of Space Traffic Management and Space Liability. Stud. Iuridica, 10.31338/2544-3135.si.2023-97.12",
            "Caja Moya, C. & Rodríguez, E. Q. (2026). International Space Environment Protection Protocol. Astropolitics, 10.1080/14777622.2026.2686075",
            "Gracin, D. et al. (2025). Ethics of Orbital Debris: Responsibility and Prevention. ELMAR, 10.1109/elmar66948.2025.11194025",
            "Guyot, J., & Rouillon, S. (2023). Sustainable management of space activity in low Earth orbit. J. Environ. Econ. Policy, 10.1080/21606544.2023.2231402",
            "Haroun, F. et al. (2021). Toward Sustainability of Outer Space: Addressing Space Debris. New Space, 10.1089/space.2020.0047",
            "Hosseini, S. et al. (2021). Space Debris Mitigation: Lessons from Environmental Law. Environ. Policy Law, 10.3233/epl-210015",
            "Jain, A., & Rao, A. (2022). International cooperation and competition in orbit-use management. ArXiv, 10.48550/arxiv.2205.03926",
            "Janikowski, A. A. (2026). Addressing Kessler Syndrome Through Market-Based Removal Obligation Trading. New Space, 10.1177/21680256261493392",
            "Li, L. (2015). Space Debris Mitigation as an International Law Obligation. Int. Community Law Rev., 10.1163/18719732-12341307",
            "Long, J. & Huang, C. (2024). Active removal of foreign space debris: global governance perspective. Acta Astronaut., 10.1016/j.actaastro.2024.06.036",
            "M, A. (2026). Artificial Space Debris Regulation: Argument for New Convention. Int. J. Space Law Policy, 10.65393/ijslpv4i12",
            "Martin-Lawson, D. et al. (2023). Cost of (Un)regulation: Shrinking Earth's orbits. J. Environ. Manage., 10.1016/j.jenvman.2023.119382",
            "Mejía-Kaiser, M. (2020). Space Law and Hazardous Space Debris. Oxford Res. Encycl., 10.1093/acrefore/9780190647926.013.70",
            "Morin, J., & Richard, B. (2021). Astro-Environmentalism: Towards Polycentric Governance of Space Debris. Glob. Policy, 10.1111/1758-5899.12950",
            "Napper, I. et al. (2025). Sustainable development goal for space: Lessons from marine debris. One Earth, 10.1016/j.oneear.2024.12.004",
            "Newman, C. & Cheney, T. (2023). Barriers and Gateways to Cleaning Up Earth Orbit. Air Space Law, 10.54648/aila2023034",
            "Pietrzak, M. (2026). Wicked Problem of Space Debris: System Dynamics View. World, 10.3390/world7020018",
            "Popova, R., & Schaus, V. (2018). Legal Framework for Space Debris Remediation as Tool for Sustainability. Aerospace, 10.3390/aerospace5020055",
            "Popova, S. S. (2025). Legal Gaps in the Definition of Space Debris. Moscow J. Int. Law, 10.24833/0869-0049-2025-2-39-48",
            "Rusconi, M., & Colombo, C. (2026). Model-based control framework for space debris management. Acta Astronaut., 10.1016/j.actaastro.2025.12.018",
            "Seffinga, V. (2024). Capitalising on Uncertainty: Proliferation of Space Debris. Glob. Jurist, 10.1515/gj-2024-0047",
            "Sheer, A. et al. (2023). Panacea to Address Legal and Economic Aspects of Debris. Adv. Space Res., 10.1016/j.asr.2023.02.023",
            "Sullivan, K., & Ben-Itzhak, S. (2023). Securing Space Domain with Active Debris Removal. Astropolitics, 10.1080/14777622.2023.2274922",
            "Svárovská, N. (2021). Common but Differentiated Responsibilities for Debris Removal. Astropolitics, 10.1080/14777622.2021.2000322",
            "Semenov, N. (2026). Legal Regime for Peaceful Use of Space (COPUOS 68th). Law & Politics, 10.7256/2454-0706.2026.3.78974",
            "Tiwari, S. et al. (2024). Space Security and the Law of Space Cooperation. IJFMR, 10.36948/ijfmr.2024.v06i05.27497"
        ]
    }
