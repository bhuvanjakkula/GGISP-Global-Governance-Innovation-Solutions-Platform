"""Unit & Integration Tests for Post-Quantum Cryptography (PQC) Subsystem.

Tests NIST FIPS 203 (ML-KEM-768), NIST FIPS 204 (ML-DSA-65), NIST FIPS 205 (SLH-DSA),
Quantum Envelope Encryption, Shor's Algorithm Threat Modeling, and Merkle Root Attestation.
"""
import pytest
from ggisp.pqc.lattice import Poly, sample_cbd, sample_uniform_poly, sha3_256, shake256
from ggisp.pqc.ml_kem import ml_kem_768, MLKEM
from ggisp.pqc.ml_dsa import ml_dsa_65, MLDSA
from ggisp.pqc.slh_dsa import slh_dsa_sha3
from ggisp.pqc.envelope import QuantumEnvelope
from ggisp.pqc.quantum_risk import calculate_shor_quantum_gates, evaluate_mosca_hndl_risk


def test_poly_ring_arithmetic():
    """Verify polynomial addition, subtraction, scalar mul, and negacyclic multiplication."""
    p1 = Poly([1, 2, 3] + [0] * 253, 256, 3329)
    p2 = Poly([4, 5, 6] + [0] * 253, 256, 3329)
    
    # Addition
    p_add = p1 + p2
    assert p_add.coeffs[0] == 5
    assert p_add.coeffs[1] == 7
    assert p_add.coeffs[2] == 9
    
    # Subtraction
    p_sub = p2 - p1
    assert p_sub.coeffs[0] == 3
    assert p_sub.coeffs[1] == 3
    assert p_sub.coeffs[2] == 3

    # Negacyclic multiplication test: X^255 * X = X^256 = -1 mod (X^256 + 1)
    p_x255 = Poly([0] * 255 + [1], 256, 3329)
    p_x1 = Poly([0, 1] + [0] * 254, 256, 3329)
    p_prod = p_x255 * p_x1
    assert p_prod.coeffs[0] == 3328  # -1 mod 3329


def test_ml_kem_encapsulation_and_decapsulation():
    """Verify NIST FIPS 203 ML-KEM-768 keypair generation, encapsulation, and shared secret recovery."""
    pk, sk = ml_kem_768.keygen()
    assert len(pk) > 0
    assert len(sk) > 0

    ciphertext, sender_ss = ml_kem_768.encapsulate(pk)
    assert len(ciphertext) > 0
    assert len(sender_ss) == 32

    # Receiver decapsulates with sk
    receiver_ss = ml_kem_768.decapsulate(sk, ciphertext)
    assert sender_ss == receiver_ss, "Shared secrets derived by sender and receiver must match identically"


def test_ml_kem_ciphertext_tampering_implicit_rejection():
    """Verify that tampering with ciphertext triggers Fujisaki-Okamoto implicit rejection."""
    pk, sk = ml_kem_768.keygen()
    ciphertext, sender_ss = ml_kem_768.encapsulate(pk)

    # Tamper with the ciphertext (flip a byte)
    tampered_ct = bytearray(ciphertext)
    tampered_ct[10] ^= 0xFF
    tampered_ct = bytes(tampered_ct)

    tampered_ss = ml_kem_768.decapsulate(sk, tampered_ct)
    assert tampered_ss != sender_ss, "Tampered ciphertext must not yield the original shared secret"


def test_ml_dsa_signature_generation_and_verification():
    """Verify NIST FIPS 204 ML-DSA-65 key generation, signing, and verification."""
    pk, sk = ml_dsa_65.keygen()
    assert len(pk) > 0
    assert len(sk) > 0

    message = b"GGISP Multilateral Sovereign Debt Restructuring Protocol 2026"
    sig = ml_dsa_65.sign(sk, message)
    assert len(sig) > 0

    # Verification must succeed
    assert ml_dsa_65.verify(pk, message, sig) is True

    # Tampered message must fail verification
    assert ml_dsa_65.verify(pk, b"Forged diplomatic message", sig) is False

    # Tampered signature must fail verification
    tampered_sig = bytearray(sig)
    tampered_sig[15] ^= 0x01
    assert ml_dsa_65.verify(pk, message, bytes(tampered_sig)) is False


def test_slh_dsa_stateless_hash_signature():
    """Verify NIST FIPS 205 SLH-DSA / WOTS+ signature scheme."""
    pk, sk = slh_dsa_sha3.keygen()
    message = b"Nuclear Safeguards Inspection Telemetry SHA3 Attestation"
    sig = slh_dsa_sha3.sign(sk, message)
    
    assert slh_dsa_sha3.verify(pk, message, sig) is True
    assert slh_dsa_sha3.verify(pk, b"Altered telemetry data", sig) is False


def test_post_quantum_envelope_encryption():
    """Verify hybrid post-quantum envelope encryption (ML-KEM-768 + AES-256-GCM)."""
    pk, sk = ml_kem_768.keygen()
    plaintext = "CONFIDENTIAL: Sovereign debt restructuring terms under G20 Common Framework"
    aad = b"PROJECT-ID-4-KENYA"

    envelope = QuantumEnvelope.encrypt_payload(pk, plaintext, associated_data=aad)
    assert envelope["pqc_standard"] == "NIST FIPS 203 (ML-KEM-768)"
    assert envelope["symmetric_cipher"] == "AES-256-GCM"

    # Decrypt
    decrypted = QuantumEnvelope.decrypt_payload(sk, envelope, associated_data=aad)
    assert decrypted.decode("utf-8") == plaintext


def test_shor_algorithm_threat_modeling():
    """Verify Shor's quantum gate and qubit calculations."""
    rsa_eval = calculate_shor_quantum_gates("RSA", 2048)
    assert rsa_eval["quantum_status"] == "VULNERABLE_TO_SHOR"
    assert rsa_eval["estimated_logical_qubits_required"] > 4000
    assert rsa_eval["post_quantum_effective_security_bits"] == 0

    ecc_eval = calculate_shor_quantum_gates("ECDSA", 256)
    assert ecc_eval["quantum_status"] == "VULNERABLE_TO_SHOR"
    assert ecc_eval["estimated_logical_qubits_required"] > 1500

    hndl = evaluate_mosca_hndl_risk()
    assert hndl["total_domains_audited"] == 13
    assert hndl["domains_with_hndl_exposure"] > 0
    assert hndl["platform_pqc_readiness_status"] == "PQC_DEPLOYED_CRYPTO_AGILE"


def test_api_pqc_endpoints(client):
    """Verify all FastAPI PQC endpoints."""
    # 1. PQC Status
    st_res = client.get("/api/pqc/status")
    assert st_res.status_code == 200
    assert st_res.json()["quantum_readiness_level"] == "PQC_ACTIVE_FIPS_COMPLIANT"

    # 2. ML-KEM Keypair & Encapsulation
    kem_kp = client.post("/api/pqc/kem/generate-keypair").json()
    assert "public_key_hex" in kem_kp
    
    enc_res = client.post("/api/pqc/kem/encapsulate", json={"public_key_hex": kem_kp["public_key_hex"]}).json()
    assert "ciphertext_hex" in enc_res
    
    dec_res = client.post("/api/pqc/kem/decapsulate", json={
        "secret_key_hex": kem_kp["secret_key_hex"],
        "ciphertext_hex": enc_res["ciphertext_hex"]
    }).json()
    assert dec_res["shared_secret_hex"] == enc_res["shared_secret_hex"]

    # 3. ML-DSA Signing & Verification
    dsa_kp = client.post("/api/pqc/dsa/generate-keypair").json()
    sign_res = client.post("/api/pqc/dsa/sign", json={
        "secret_key_hex": dsa_kp["secret_key_hex"],
        "message": "Quantum policy covenant"
    }).json()
    
    verify_res = client.post("/api/pqc/dsa/verify", json={
        "public_key_hex": dsa_kp["public_key_hex"],
        "message": "Quantum policy covenant",
        "signature_hex": sign_res["signature_hex"]
    }).json()
    assert verify_res["verified"] is True

    # 4. Hybrid Envelope Encryption
    env_res = client.post("/api/pqc/envelope/encrypt", json={
        "public_key_hex": kem_kp["public_key_hex"],
        "plaintext": "Top Secret Multilateral Treaty Text"
    }).json()
    
    dec_env = client.post("/api/pqc/envelope/decrypt", json={
        "secret_key_hex": kem_kp["secret_key_hex"],
        "envelope": env_res
    }).json()
    assert dec_env["plaintext"] == "Top Secret Multilateral Treaty Text"

    # 5. Shor & Mosca Risk Audit
    shor_res = client.get("/api/pqc/shor-risk-audit")
    assert shor_res.status_code == 200
    assert len(shor_res.json()["domain_audits"]) == 13

    # 6. Post-Quantum Merkle Root Signing
    merkle_pqc = client.post("/api/pqc/sign-merkle-root")
    assert merkle_pqc.status_code == 200
    m_data = merkle_pqc.json()
    assert m_data["signature_verification"] is True
    assert m_data["attestation_status"] == "POST_QUANTUM_MERKLE_ROOT_SIGNED_AND_AUTHENTICATED"
