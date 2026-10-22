"""Specialist Engine 6: Defensive Cyber Resilience & Post-Quantum Cryptography Migration Index.
Reference: ITU Global Cybersecurity Index (GCI) / NIST Post-Quantum Cryptographic Standards (FIPS 203/204).
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class CyberDefenseInput(BaseModel):
    country_code: str = Field(default="KEN", min_length=2, max_length=5)
    critical_infrastructure_sectors_protected: int = Field(default=8, ge=1, le=16, description="Sectors covered by mandatory defensive controls")
    national_csirt_incident_response_hours: float = Field(default=4.5, ge=0.5, le=72.0, description="Average response latency to Tier-1 critical attacks")
    post_quantum_migration_progress_percent: float = Field(default=15.0, ge=0.0, le=100.0, description="PQC algorithms implemented (Kyber/Dilithium/Sphincs+)")
    data_shelf_life_security_years: int = Field(default=15, ge=5, le=50, description="Years sensitive national data must remain confidential (X)")
    pqc_migration_duration_years: int = Field(default=7, ge=2, le=20, description="Years required to fully migrate cryptographic architecture (Y)")
    estimated_years_to_cryptanalytic_quantum: int = Field(default=10, ge=5, le=30, description="Years until Quantum Computer breaks RSA/ECC (Z)")

    # Collective Cyber Defense & Collaborative CTI Sharing (Skopik et al. 2016; Husák et al. 2022; Ayogu 2025)
    collective_defense_architecture: str = Field(
        default="crusoe_ooda_loop",
        description="Collaborative framework: crusoe_ooda_loop, defensechain_blockchain, isas_macro_infrastructure, attack_d3fend_pipeline, three_layer_bayesian_model"
    )
    threat_intelligence_sharing_paradigm: str = Field(
        default="confidential_computing_enclave",
        description="CTI sharing mode: confidential_computing_enclave, decentralized_data_space, automated_stix_taxii, centralized_isac"
    )
    enable_automated_peer_scoring: bool = Field(default=True, description="Mitigates free-riding and validates submitted telemetry via consensus scoring")


def simulate_cyber_defense(inp: CyberDefenseInput) -> Dict[str, Any]:
    """Calculate National Cyber Resilience Index, evaluate Mosca's Theorem for PQC, and model collective defense architecture."""
    # Mosca's Theorem: If X + Y > Z, data is vulnerable to "Harvest Now, Decrypt Later" (HNDL) attacks today!
    x = inp.data_shelf_life_security_years
    y = inp.pqc_migration_duration_years
    z = inp.estimated_years_to_cryptanalytic_quantum

    mosca_sum = x + y
    is_quantum_vulnerable_now = mosca_sum > z
    vulnerability_gap_years = max(mosca_sum - z, 0)

    # National Cyber Resilience Score (0 to 100):
    sector_score = (inp.critical_infrastructure_sectors_protected / 16.0) * 35.0
    latency_score = max(35.0 - (inp.national_csirt_incident_response_hours * 0.7), 5.0)
    pqc_score = (inp.post_quantum_migration_progress_percent / 100.0) * 30.0
    resilience_index = round(sector_score + latency_score + pqc_score, 1)

    # Collaborative Cyber Defense Decision Support Paradigm (Husák et al. 2022; Jo et al. 2026; Purohit et al. 2023):
    arch = inp.collective_defense_architecture.lower().strip()
    if arch == "crusoe_ooda_loop":
        framework_eval = {
            "framework_name": "CRUSOE Cyber Situational Awareness Toolset (Husák et al. 2022)",
            "operational_methodology": "Continuous OODA loop (Observe, Orient, Decide, Act) for multi-phase incident triage",
            "strategic_capability": "Correlates local network indicators with mission objectives to recommend resilient infrastructure reconfigurations."
        }
    elif arch == "defensechain_blockchain":
        framework_eval = {
            "framework_name": "DefenseChain Smart Contract Consortium (Purohit et al. 2023)",
            "operational_methodology": "Consortium smart contracts with peer scoring and economic incentives",
            "strategic_capability": "Eliminates free-riding and incentivizes cross-domain validation of threat mitigations."
        }
    elif arch == "isas_macro_infrastructure":
        framework_eval = {
            "framework_name": "ISAS National Macro-Mission Architecture (Imanimehr et al. 2025)",
            "operational_methodology": "Sector-specific risk aggregation across interconnected national critical infrastructure",
            "strategic_capability": "Quantifies interconnected dependency cascades across energy, finance, and telecommunications grids."
        }
    elif arch == "attack_d3fend_pipeline":
        framework_eval = {
            "framework_name": "Proactive ATT&CK–D3FEND Pipeline (Jo et al. 2026)",
            "operational_methodology": "LLM-driven mapping of adversary tactic sequences directly to defensive countermeasures",
            "strategic_capability": "Generates real-time machine-executable countermeasures from unstructured CTI feeds."
        }
    else:  # three_layer_bayesian_model
        framework_eval = {
            "framework_name": "Three-Layer Bayesian Conflict Model (Requena Micó et al. 2026)",
            "operational_methodology": "Bayesian event networks integrated with systemic attack graphs",
            "strategic_capability": "Balances residual mission risk against operational defensive costs and defensive latency."
        }

    # Threat Intelligence Sharing & Privacy-Preserving Enclave Assessment (Ayogu 2025; Gurabi et al. 2025):
    sharing_mode = inp.threat_intelligence_sharing_paradigm.lower().strip()
    if sharing_mode == "confidential_computing_enclave":
        sharing_evaluation = {
            "mode": "Confidential Computing Threat Exchange (Ayogu 2025)",
            "sovereignty_protection": "Hardware-enforced secure enclaves permit real-time threat telemetry correlation without exposing proprietary payloads.",
            "bottleneck_mitigation": "Automated cross-sector ingestion suppresses manual email/form latency by > 90%."
        }
    elif sharing_mode == "decentralized_data_space":
        sharing_evaluation = {
            "mode": "Decentralized CTI Data Space (Gurabi et al. 2025)",
            "sovereignty_protection": "Formal usage control and sovereign metadata connectors prevent unauthorized downstream redistribution.",
            "bottleneck_mitigation": "Peer-to-peer data sovereignty preserves compliance with national privacy and trade secret laws."
        }
    else:
        sharing_evaluation = {
            "mode": "Automated STIX/TAXII Pipeline (Leitner et al. 2024)",
            "sovereignty_protection": "Standardized syntactic protocol for machine-to-machine exchange across CSIRTs and ISACs.",
            "bottleneck_mitigation": "Eliminates human-in-the-loop triage delays during high-tempo coordinated intrusions."
        }

    return {
        "engine": "Defensive Cyber Resilience & Quantum Migration Matrix",
        "domain": "cybersecurity",
        "country_code": inp.country_code,
        "national_cyber_resilience_index_100": resilience_index,
        "collective_cyber_defense": {
            "operational_framework": framework_eval,
            "threat_sharing_architecture": sharing_evaluation,
            "peer_validation_scoring_active": inp.enable_automated_peer_scoring,
            "situational_awareness_uplift": "Significant empirical uplift: aggregates heterogeneous telemetry to transition from reactive patching to proactive national early warning."
        },
        "mosca_quantum_theorem_evaluation": {
            "data_confidentiality_shelf_life_years_X": x,
            "pqc_migration_timeline_years_Y": y,
            "years_to_quantum_threat_Z": z,
            "harvest_now_decrypt_later_vulnerability": is_quantum_vulnerable_now,
            "exposure_window_years": vulnerability_gap_years,
        },
        "post_quantum_readiness_status": (
            "CRITICAL EXPOSURE: Immediate transition to NIST FIPS 203 (ML-KEM) and FIPS 204 (ML-DSA) required to prevent retroactive decryption."
            if is_quantum_vulnerable_now
            else "ADEQUATE MIGRATION WINDOW: Transition plan on track to outpace quantum cryptanalytic breakthroughs."
        ),
        "cooperation_framework": "UN OEWG Cyber Norms, ITU Global Cybersecurity Index, and Multi-Level Collaborative Cyber Situational Awareness (MCF-CSA).",
        "literature_citations": [
            "Skopik, F. et al. (2016). Collective cyber defense through security information sharing. Comput. Secur., 10.1016/j.cose.2016.04.003",
            "Husák, M. et al. (2022). CRUSOE: toolset for cyber situational awareness and decision support. Comput. Secur., 10.1016/j.cose.2022.102609",
            "Ayogu, W. C. (2025). Confidential Computing Threat Exchange. IJSRMT, 10.38124/ijsrmt.v4i9.809",
            "Gurabi, M. A. et al. (2025). Enhancing CTI Sharing through Data Spaces. IEEE CSR, 10.1109/csr64739.2025.11130001",
            "Purohit, S. et al. (2023). Cyber Threat Intelligence Sharing for Co-Operative Defense. IEEE TDSC, 10.1109/tdsc.2022.3214423",
            "Jo, R. et al. (2026). Proactive Cyber Defense with ATT&CK-D3FEND Mapping. Systems, 10.3390/systems14050575",
            "Requena Micó, M. et al. (2026). A Three-Layer Cyber Defense Scenario Model. Springer, 10.1007/978-3-032-35579-9_20"
        ]
    }

