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


def simulate_cyber_defense(inp: CyberDefenseInput) -> Dict[str, Any]:
    """Calculate National Cyber Resilience Index and evaluate Mosca's Theorem for quantum threat."""
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

    return {
        "engine": "Defensive Cyber Resilience & Quantum Migration Matrix",
        "domain": "cybersecurity",
        "country_code": inp.country_code,
        "national_cyber_resilience_index_100": resilience_index,
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
        "cooperation_framework": "UN OEWG Confidence-Building Measures & ITU Global Cybersecurity Index Architecture.",
    }
