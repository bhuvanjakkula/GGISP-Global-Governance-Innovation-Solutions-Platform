"""Post-Quantum Cryptography (PQC) Subsystem for GGISP Platform.

Implements NIST FIPS 203 (ML-KEM), NIST FIPS 204 (ML-DSA), NIST FIPS 205 (SLH-DSA),
hybrid envelope encryption, Shor's algorithm threat modeling, and quantum-resilient Merkle root attestation.
"""
from ggisp.pqc.envelope import QuantumEnvelope
from ggisp.pqc.ml_dsa import ml_dsa_65
from ggisp.pqc.ml_kem import ml_kem_768
from ggisp.pqc.quantum_risk import calculate_shor_quantum_gates, evaluate_mosca_hndl_risk
from ggisp.pqc.router import router as pqc_router
from ggisp.pqc.slh_dsa import slh_dsa_sha3

__all__ = [
    "pqc_router",
    "ml_kem_768",
    "ml_dsa_65",
    "slh_dsa_sha3",
    "QuantumEnvelope",
    "evaluate_mosca_hndl_risk",
    "calculate_shor_quantum_gates",
]
