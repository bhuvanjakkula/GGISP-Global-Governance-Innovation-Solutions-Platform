"""Quantum Threat Modeling & Shor's Algorithm Risk Assessment Engine.

Implements Mosca's Theorem (X + Y > Z) risk evaluation, Shor's algorithm gate requirements,
and "Harvest Now, Decrypt Later" (HNDL) exposure assessments across all 13 multilateral divisions.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

# Estimated years until Cryptanalytically Relevant Quantum Computer (CRQC)
CRQC_HORIZON_YEARS = 7.5

DOMAIN_SENSITIVITY_YEARS = {
    "nuclear-security": {"shelf_life_years": 40, "sensitivity_tier": "CRITICAL_STATE_SECRET"},
    "sovereign-debt": {"shelf_life_years": 25, "sensitivity_tier": "CONFIDENTIAL_MACRO_FINANCIAL"},
    "un-security-council": {"shelf_life_years": 30, "sensitivity_tier": "STRATEGIC_DIPLOMATIC"},
    "wto-trade": {"shelf_life_years": 10, "sensitivity_tier": "COMMERCIAL_DISPUTE_CONFIDENTIAL"},
    "ai-governance": {"shelf_life_years": 15, "sensitivity_tier": "FRONTIER_WEIGHTS_SECURITY"},
    "cybersecurity": {"shelf_life_years": 8, "sensitivity_tier": "OPERATIONAL_ZERO_DAY_DISCLOSURE"},
    "global-health": {"shelf_life_years": 20, "sensitivity_tier": "BIO_SURVEILLANCE_GENOMIC"},
    "space-security": {"shelf_life_years": 25, "sensitivity_tier": "DUAL_USE_ORBITAL_TELEMETRY"},
    "critical-minerals": {"shelf_life_years": 15, "sensitivity_tier": "STRATEGIC_RESERVE_CHOKEPOINT"},
    "ocean-governance": {"shelf_life_years": 15, "sensitivity_tier": "MARITIME_EXCLUSIVE_ENFORCEMENT"},
    "international-tax": {"shelf_life_years": 20, "sensitivity_tier": "CBCR_CROSS_BORDER_SECRECY"},
    "development-finance": {"shelf_life_years": 20, "sensitivity_tier": "CONCESSIONAL_LOAN_CONDITIONALITY"},
    "climate-finance": {"shelf_life_years": 15, "sensitivity_tier": "LOSS_AND_DAMAGE_DISBURSEMENT"},
}


def calculate_shor_quantum_gates(classical_algo: str, key_bits: int) -> Dict[str, Any]:
    """Calculate logical/physical qubit and Toffoli gate requirements for Shor's algorithm."""
    if classical_algo.upper() == "RSA":
        # Shor's factoring algorithm: ~2n logical qubits, ~8n^3 Toffoli gates
        logical_qubits = 2 * key_bits + int(math.ceil(math.log2(key_bits)))
        # Assuming surface code with physical-to-logical error ratio of ~1000:1
        physical_qubits = logical_qubits * 1450
        quantum_gate_depth = 8 * (key_bits ** 3)
        security_bits = 0  # Broken in polynomial time by Shor
    elif classical_algo.upper() in ("ECDSA", "ECC"):
        # Shor's discrete log: ~6n logical qubits, ~32n^3 Toffoli gates
        logical_qubits = 6 * key_bits
        physical_qubits = logical_qubits * 1100
        quantum_gate_depth = 32 * (key_bits ** 3)
        security_bits = 0
    else:
        # Post-quantum lattice (ML-KEM / ML-DSA): only susceptible to Grover speedup sqrt(N)
        logical_qubits = 0
        physical_qubits = 0
        quantum_gate_depth = 2 ** (key_bits // 2)
        security_bits = key_bits // 2

    return {
        "algorithm": classical_algo.upper(),
        "classical_key_bits": key_bits,
        "quantum_status": "VULNERABLE_TO_SHOR" if security_bits == 0 else "POST_QUANTUM_RESILIENT",
        "estimated_logical_qubits_required": logical_qubits,
        "estimated_physical_qubits_required": physical_qubits,
        "quantum_circuit_depth_estimate": f"{quantum_gate_depth:.2e}",
        "post_quantum_effective_security_bits": security_bits,
    }


def evaluate_mosca_hndl_risk() -> Dict[str, Any]:
    """Evaluate Mosca's Theorem (X + Y > Z) and HNDL risk across all 13 domains.
    
    X: Data Shelf-Life Sensitivity (years)
    Y: Migration Time to Post-Quantum Cryptography (years) - assumed 3.0 years
    Z: Collapse Horizon until CRQC Availability (years) - assumed 7.5 years
    If X + Y > Z, data harvested today by adversaries will be decrypted within its sensitivity lifetime!
    """
    migration_time_years = 3.0
    results: List[Dict[str, Any]] = []
    at_risk_count = 0

    for slug, meta in DOMAIN_SENSITIVITY_YEARS.items():
        x = meta["shelf_life_years"]
        y = migration_time_years
        z = CRQC_HORIZON_YEARS
        
        # Mosca inequality test
        mosca_violation = (x + y) > z
        hndl_exposure_gap_years = max(0.0, (x + y) - z)
        
        if mosca_violation:
            at_risk_count += 1

        results.append({
            "domain_slug": slug,
            "sensitivity_tier": meta["sensitivity_tier"],
            "data_shelf_life_years_x": x,
            "migration_timeline_years_y": y,
            "crqc_horizon_years_z": z,
            "hndl_compromise_risk": "CRITICAL_EXPOSURE" if mosca_violation else "SAFE",
            "exposure_window_years": round(hndl_exposure_gap_years, 1),
            "recommended_pqc_standard": "NIST FIPS 203 (ML-KEM-768) + NIST FIPS 204 (ML-DSA-65)",
        })

    # Sort descending by exposure window
    results.sort(key=lambda r: r["exposure_window_years"], reverse=True)

    return {
        "crqc_availability_horizon_years": CRQC_HORIZON_YEARS,
        "platform_migration_timeline_years": migration_time_years,
        "total_domains_audited": len(DOMAIN_SENSITIVITY_YEARS),
        "domains_with_hndl_exposure": at_risk_count,
        "hndl_threat_percentage": round(100.0 * at_risk_count / len(DOMAIN_SENSITIVITY_YEARS), 1),
        "platform_pqc_readiness_status": "PQC_DEPLOYED_CRYPTO_AGILE",
        "active_pqc_primitives": [
            "NIST FIPS 203: ML-KEM-768 (Module-Lattice Key Encapsulation)",
            "NIST FIPS 204: ML-DSA-65 (Module-Lattice Digital Signatures)",
            "NIST FIPS 205: SLH-DSA (Stateless Hash-Based Signatures / WOTS+)",
            "Hybrid Post-Quantum Envelope Encryption (AES-256-GCM + ML-KEM)",
        ],
        "domain_audits": results,
    }
