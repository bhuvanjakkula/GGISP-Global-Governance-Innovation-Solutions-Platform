"""Hybrid Post-Quantum Envelope Encryption.

Combines NIST FIPS 203 (ML-KEM-768) post-quantum key encapsulation with
AES-256-GCM authenticated symmetric encryption for confidential research dossiers,
empirical datasets, and sovereign policy proposals.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ggisp.pqc.ml_kem import ml_kem_768


class QuantumEnvelope:
    """Post-Quantum Envelope Encryption Service."""

    @staticmethod
    def encrypt_payload(
        public_key_bytes: bytes,
        plaintext: str | bytes,
        associated_data: bytes = b"GGISP-PQC-ENVELOPE-v1",
    ) -> Dict[str, Any]:
        """Encrypt payload using ML-KEM-768 key encapsulation and AES-256-GCM."""
        if isinstance(plaintext, str):
            payload_bytes = plaintext.encode("utf-8")
        else:
            payload_bytes = plaintext

        # 1. Encapsulate post-quantum shared secret (32 bytes = 256 bits)
        kem_ciphertext, shared_secret = ml_kem_768.encapsulate(public_key_bytes)

        # 2. Encrypt payload with AES-256-GCM using the post-quantum key
        aesgcm = AESGCM(shared_secret)
        nonce = secrets.token_bytes(12)  # 96-bit standard GCM nonce
        encrypted_data = aesgcm.encrypt(nonce, payload_bytes, associated_data)

        # Separate ciphertext and GCM tag (last 16 bytes in cryptography library)
        ciphertext = encrypted_data[:-16]
        tag = encrypted_data[-16:]

        return {
            "pqc_standard": "NIST FIPS 203 (ML-KEM-768)",
            "symmetric_cipher": "AES-256-GCM",
            "security_level": "NIST Category 3 (192-bit Quantum-Secure)",
            "kem_ciphertext": kem_ciphertext.hex(),
            "nonce": nonce.hex(),
            "tag": tag.hex(),
            "ciphertext": ciphertext.hex(),
            "associated_data": associated_data.decode("utf-8", errors="ignore"),
            "payload_bytes_len": len(payload_bytes),
        }

    @staticmethod
    def decrypt_payload(
        secret_key_bytes: bytes,
        envelope_data: Dict[str, Any],
        associated_data: bytes = b"GGISP-PQC-ENVELOPE-v1",
    ) -> bytes:
        """Decrypt post-quantum envelope using ML-KEM-768 secret key."""
        kem_ciphertext = bytes.fromhex(envelope_data["kem_ciphertext"])
        nonce = bytes.fromhex(envelope_data["nonce"])
        tag = bytes.fromhex(envelope_data["tag"])
        ciphertext = bytes.fromhex(envelope_data["ciphertext"])

        # 1. Decapsulate post-quantum shared secret
        shared_secret = ml_kem_768.decapsulate(secret_key_bytes, kem_ciphertext)

        # 2. Decrypt with AES-256-GCM
        aesgcm = AESGCM(shared_secret)
        full_ciphertext = ciphertext + tag
        return aesgcm.decrypt(nonce, full_ciphertext, associated_data)
