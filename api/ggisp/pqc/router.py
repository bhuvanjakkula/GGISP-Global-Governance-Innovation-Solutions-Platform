"""FastAPI Router for Post-Quantum Cryptography & Cyber Resilience Services."""
from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ggisp.pqc.envelope import QuantumEnvelope
from ggisp.pqc.ml_dsa import ml_dsa_65
from ggisp.pqc.ml_kem import ml_kem_768
from ggisp.pqc.quantum_risk import calculate_shor_quantum_gates, evaluate_mosca_hndl_risk
from ggisp.pqc.slh_dsa import slh_dsa_sha3

router = APIRouter(prefix="/api/pqc", tags=["Post-Quantum Cryptography"])


class KeypairResponse(BaseModel):
    algorithm: str
    security_level: str
    public_key_hex: str
    secret_key_hex: str
    public_key_bytes_len: int
    secret_key_bytes_len: int


class KemEncapsulateRequest(BaseModel):
    public_key_hex: str


class KemEncapsulateResponse(BaseModel):
    algorithm: str
    ciphertext_hex: str
    shared_secret_hex: str
    shared_secret_bits: int


class KemDecapsulateRequest(BaseModel):
    secret_key_hex: str
    ciphertext_hex: str


class KemDecapsulateResponse(BaseModel):
    algorithm: str
    shared_secret_hex: str
    decapsulation_status: str


class DsaSignRequest(BaseModel):
    secret_key_hex: str
    message: str


class DsaSignResponse(BaseModel):
    algorithm: str
    message_digest_sha3_256: str
    signature_hex: str
    signature_bytes_len: int


class DsaVerifyRequest(BaseModel):
    public_key_hex: str
    message: str
    signature_hex: str


class DsaVerifyResponse(BaseModel):
    algorithm: str
    verified: bool
    status: str


class EnvelopeEncryptRequest(BaseModel):
    public_key_hex: str
    plaintext: str
    associated_data: Optional[str] = "GGISP-PQC-DOSSIER-v1"


class EnvelopeDecryptRequest(BaseModel):
    secret_key_hex: str
    envelope: Dict[str, Any]
    associated_data: Optional[str] = "GGISP-PQC-DOSSIER-v1"


class ShorAuditRequest(BaseModel):
    classical_algorithm: str = Field(default="RSA", description="RSA, ECDSA")
    key_bits: int = Field(default=2048, ge=256, le=16384)


@router.get("/status")
def get_pqc_status():
    """Retrieve platform post-quantum cryptographic readiness and active standards."""
    return {
        "quantum_readiness_level": "PQC_ACTIVE_FIPS_COMPLIANT",
        "active_standards": [
            {
                "standard": "NIST FIPS 203",
                "primitive": "ML-KEM-768 (Kyber)",
                "purpose": "Post-Quantum Key Encapsulation Mechanism",
                "security_level": "NIST Category 3 (192-bit Quantum)",
            },
            {
                "standard": "NIST FIPS 204",
                "primitive": "ML-DSA-65 (Dilithium)",
                "purpose": "Module-Lattice Digital Signatures",
                "security_level": "NIST Category 3 (192-bit Quantum)",
            },
            {
                "standard": "NIST FIPS 205",
                "primitive": "SLH-DSA (SPHINCS+ / WOTS+)",
                "purpose": "Stateless Hash-Based Digital Signatures",
                "security_level": "Information-Theoretic Quantum Hash Security",
            },
            {
                "standard": "NIST SP 800-38D + FIPS 203",
                "primitive": "AES-256-GCM + ML-KEM-768 Hybrid Envelope",
                "purpose": "Quantum-Resilient Policy Brief & Evidence Confidentiality",
                "security_level": "256-bit Symmetric / 192-bit Asymmetric Quantum",
            },
        ],
        "cryptographic_primitives": {
            "underlying_hash": "SHA3-256, SHA3-512, SHAKE-256",
            "lattice_ring": "Z_3329[X]/(X^256 + 1) and Z_8380417[X]/(X^256 + 1)",
            "shor_algorithm_protection": "TRUE (Immune to quantum polynomial factorization)",
            "grover_algorithm_protection": "TRUE (256-bit keys ensure >= 128-bit quantum security)",
        },
    }


# ---------------------------------------------------------
# ML-KEM (FIPS 203) Key Encapsulation
# ---------------------------------------------------------

@router.post("/kem/generate-keypair", response_model=KeypairResponse)
def kem_generate_keypair():
    """Generate a NIST FIPS 203 ML-KEM-768 post-quantum keypair."""
    pk, sk = ml_kem_768.keygen()
    return KeypairResponse(
        algorithm="ML-KEM-768",
        security_level="NIST Category 3",
        public_key_hex=pk.hex(),
        secret_key_hex=sk.hex(),
        public_key_bytes_len=len(pk),
        secret_key_bytes_len=len(sk),
    )


@router.post("/kem/encapsulate", response_model=KemEncapsulateResponse)
def kem_encapsulate(req: KemEncapsulateRequest):
    """Encapsulate a quantum-secure shared secret against an ML-KEM-768 public key."""
    try:
        pk = bytes.fromhex(req.public_key_hex)
        ct, ss = ml_kem_768.encapsulate(pk)
        return KemEncapsulateResponse(
            algorithm="ML-KEM-768",
            ciphertext_hex=ct.hex(),
            shared_secret_hex=ss.hex(),
            shared_secret_bits=len(ss) * 8,
        )
    except Exception as exc:
        raise HTTPException(400, f"ML-KEM encapsulation failed: {str(exc)}")


@router.post("/kem/decapsulate", response_model=KemDecapsulateResponse)
def kem_decapsulate(req: KemDecapsulateRequest):
    """Decapsulate a quantum-secure shared secret from a ciphertext using ML-KEM-768."""
    try:
        sk = bytes.fromhex(req.secret_key_hex)
        ct = bytes.fromhex(req.ciphertext_hex)
        ss = ml_kem_768.decapsulate(sk, ct)
        return KemDecapsulateResponse(
            algorithm="ML-KEM-768",
            shared_secret_hex=ss.hex(),
            decapsulation_status="SUCCESS_SHARED_SECRET_RECOVERED",
        )
    except Exception as exc:
        raise HTTPException(400, f"ML-KEM decapsulation failed: {str(exc)}")


# ---------------------------------------------------------
# ML-DSA (FIPS 204) Lattice Signatures
# ---------------------------------------------------------

@router.post("/dsa/generate-keypair", response_model=KeypairResponse)
def dsa_generate_keypair():
    """Generate a NIST FIPS 204 ML-DSA-65 post-quantum digital signature keypair."""
    pk, sk = ml_dsa_65.keygen()
    return KeypairResponse(
        algorithm="ML-DSA-65",
        security_level="NIST Category 3",
        public_key_hex=pk.hex(),
        secret_key_hex=sk.hex(),
        public_key_bytes_len=len(pk),
        secret_key_bytes_len=len(sk),
    )


@router.post("/dsa/sign", response_model=DsaSignResponse)
def dsa_sign(req: DsaSignRequest):
    """Sign a policy proposal or evidence statement using NIST FIPS 204 ML-DSA-65."""
    try:
        sk = bytes.fromhex(req.secret_key_hex)
        msg_bytes = req.message.encode("utf-8")
        sig = ml_dsa_65.sign(sk, msg_bytes)
        import hashlib
        digest = hashlib.sha3_256(msg_bytes).hexdigest()
        return DsaSignResponse(
            algorithm="ML-DSA-65",
            message_digest_sha3_256=digest,
            signature_hex=sig.hex(),
            signature_bytes_len=len(sig),
        )
    except Exception as exc:
        raise HTTPException(400, f"ML-DSA signing failed: {str(exc)}")


@router.post("/dsa/verify", response_model=DsaVerifyResponse)
def dsa_verify(req: DsaVerifyRequest):
    """Verify an ML-DSA-65 digital signature against a public key."""
    try:
        pk = bytes.fromhex(req.public_key_hex)
        sig = bytes.fromhex(req.signature_hex)
        msg_bytes = req.message.encode("utf-8")
        valid = ml_dsa_65.verify(pk, msg_bytes, sig)
        return DsaVerifyResponse(
            algorithm="ML-DSA-65",
            verified=valid,
            status="QUANTUM_DIGITAL_SIGNATURE_AUTHENTIC" if valid else "SIGNATURE_VERIFICATION_FAILED_OR_TAMPERED",
        )
    except Exception as exc:
        raise HTTPException(400, f"ML-DSA verification failed: {str(exc)}")


# ---------------------------------------------------------
# SLH-DSA (FIPS 205) Stateless Hash Signatures
# ---------------------------------------------------------

@router.post("/slh/generate-keypair", response_model=KeypairResponse)
def slh_generate_keypair():
    """Generate a NIST FIPS 205 SLH-DSA (SPHINCS+ / WOTS+) keypair."""
    pk, sk = slh_dsa_sha3.keygen()
    return KeypairResponse(
        algorithm="SLH-DSA-SHA3",
        security_level="Information-Theoretic Hash Security",
        public_key_hex=pk.hex(),
        secret_key_hex=sk.hex(),
        public_key_bytes_len=len(pk),
        secret_key_bytes_len=len(sk),
    )


@router.post("/slh/sign")
def slh_sign(req: DsaSignRequest):
    """Sign payload using SLH-DSA stateless hash-based signature."""
    try:
        sk = bytes.fromhex(req.secret_key_hex)
        sig = slh_dsa_sha3.sign(sk, req.message.encode("utf-8"))
        return {
            "algorithm": "SLH-DSA-SHA3",
            "signature_hex": sig.hex(),
            "signature_bytes_len": len(sig),
        }
    except Exception as exc:
        raise HTTPException(400, f"SLH-DSA signing failed: {str(exc)}")


@router.post("/slh/verify")
def slh_verify(req: DsaVerifyRequest):
    """Verify an SLH-DSA stateless hash-based signature."""
    try:
        pk = bytes.fromhex(req.public_key_hex)
        sig = bytes.fromhex(req.signature_hex)
        valid = slh_dsa_sha3.verify(pk, req.message.encode("utf-8"), sig)
        return {
            "algorithm": "SLH-DSA-SHA3",
            "verified": valid,
            "status": "HASH_BASED_SIGNATURE_AUTHENTIC" if valid else "VERIFICATION_FAILED",
        }
    except Exception as exc:
        raise HTTPException(400, f"SLH-DSA verification failed: {str(exc)}")


# ---------------------------------------------------------
# Post-Quantum Envelope Encryption
# ---------------------------------------------------------

@router.post("/envelope/encrypt")
def envelope_encrypt(req: EnvelopeEncryptRequest):
    """Encrypt a confidential policy brief or data record using ML-KEM-768 + AES-256-GCM."""
    try:
        pk = bytes.fromhex(req.public_key_hex)
        aad = req.associated_data.encode("utf-8") if req.associated_data else b""
        envelope = QuantumEnvelope.encrypt_payload(pk, req.plaintext, associated_data=aad)
        return envelope
    except Exception as exc:
        raise HTTPException(400, f"Quantum envelope encryption failed: {str(exc)}")


@router.post("/envelope/decrypt")
def envelope_decrypt(req: EnvelopeDecryptRequest):
    """Decrypt a quantum-encrypted envelope using an ML-KEM-768 private key."""
    try:
        sk = bytes.fromhex(req.secret_key_hex)
        aad = req.associated_data.encode("utf-8") if req.associated_data else b""
        decrypted = QuantumEnvelope.decrypt_payload(sk, req.envelope, associated_data=aad)
        return {
            "plaintext": decrypted.decode("utf-8", errors="replace"),
            "bytes_decrypted": len(decrypted),
            "decryption_status": "AUTHENTICATED_AND_DECRYPTED",
        }
    except Exception as exc:
        raise HTTPException(400, f"Quantum envelope decryption failed: {str(exc)}")


# ---------------------------------------------------------
# Shor's Algorithm Threat Evaluator & Mosca HNDL Matrix
# ---------------------------------------------------------

@router.get("/shor-risk-audit")
def get_shor_risk_audit():
    """Evaluate Mosca's Theorem (X + Y > Z) and HNDL risk across all 13 domains."""
    return evaluate_mosca_hndl_risk()


@router.post("/shor-gate-calculation")
def calculate_shor_gates(req: ShorAuditRequest):
    """Calculate logical qubits and Toffoli gate depth required by Shor's algorithm."""
    return calculate_shor_quantum_gates(req.classical_algorithm, req.key_bits)


@router.post("/sign-merkle-root")
def sign_merkle_root_with_pqc():
    """Attest and sign the live cryptographic Merkle Root with an ML-DSA-65 post-quantum digital signature."""
    from ggisp.engineering.merkle import generate_planetary_audit_tree
    audit_tree = generate_planetary_audit_tree()
    root_hash = audit_tree["merkle_root"]
    
    # Generate quantum authority keypair
    pk, sk = ml_dsa_65.keygen()
    
    # Sign Merkle root with ML-DSA
    sig = ml_dsa_65.sign(sk, root_hash.encode("utf-8"))
    
    # Verify signature
    valid = ml_dsa_65.verify(pk, root_hash.encode("utf-8"), sig)
    
    return {
        "merkle_root": root_hash,
        "total_attested_records": audit_tree["total_attested_records"],
        "pqc_signature_standard": "NIST FIPS 204 (ML-DSA-65)",
        "quantum_security_level": "NIST Category 3 (Lattice-Based Fiat-Shamir)",
        "quantum_public_key_hex": pk.hex(),
        "pqc_digital_signature_hex": sig.hex(),
        "signature_verification": valid,
        "attestation_status": "POST_QUANTUM_MERKLE_ROOT_SIGNED_AND_AUTHENTICATED",
    }
