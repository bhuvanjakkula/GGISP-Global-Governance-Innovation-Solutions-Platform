"""NIST FIPS 203: Module-Lattice Key Encapsulation Mechanism (ML-KEM / Kyber).

Implements ML-KEM-512, ML-KEM-768, and ML-KEM-1024 with IND-CCA2 security
via the Fujisaki-Okamoto transform and implicit rejection.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from typing import Dict, NamedTuple, Tuple

from ggisp.pqc.lattice import (
    KYBER_N,
    KYBER_Q,
    Poly,
    sample_cbd,
    sample_uniform_poly,
    sha3_256,
    sha3_512,
    shake256,
)


class MLKEMParams(NamedTuple):
    name: str
    k: int
    eta1: int
    eta2: int
    du: int
    dv: int


PARAMS_512 = MLKEMParams("ML-KEM-512", k=2, eta1=3, eta2=2, du=10, dv=4)
PARAMS_768 = MLKEMParams("ML-KEM-768", k=3, eta1=2, eta2=2, du=10, dv=4)
PARAMS_1024 = MLKEMParams("ML-KEM-1024", k=4, eta1=2, eta2=2, du=11, dv=5)


def encode_message_to_poly(msg: bytes) -> Poly:
    """Encode 32-byte message into polynomial coefficients: bit * round(q/2)."""
    coeffs = []
    half_q = (KYBER_Q + 1) // 2
    for byte in msg:
        for bit_idx in range(8):
            bit = (byte >> bit_idx) & 1
            coeffs.append(half_q if bit else 0)
    return Poly(coeffs, KYBER_N, KYBER_Q)


def decode_poly_to_message(p: Poly) -> bytes:
    """Decode polynomial coefficients back into 32-byte message."""
    msg = bytearray(32)
    half_q = KYBER_Q // 2
    quarter_q = KYBER_Q // 4
    three_quarter_q = (3 * KYBER_Q) // 4
    
    for i, c in enumerate(p.coeffs):
        # Round c / (q/2) to nearest bit
        bit = 1 if (quarter_q <= c < three_quarter_q) else 0
        byte_idx = i // 8
        bit_idx = i % 8
        msg[byte_idx] |= (bit << bit_idx)
    return bytes(msg)


class MLKEM:
    """NIST FIPS 203 Module-Lattice Key Encapsulation Mechanism."""

    def __init__(self, params: MLKEMParams = PARAMS_768):
        self.params = params
        self.k = params.k
        self.eta1 = params.eta1
        self.eta2 = params.eta2
        self.du = params.du
        self.dv = params.dv

    def _sample_matrix(self, rho: bytes, transpose: bool = False) -> list[list[Poly]]:
        """Sample k x k matrix of polynomials from seed rho."""
        mat = []
        for i in range(self.k):
            row = []
            for j in range(self.k):
                ii, jj = (j, i) if transpose else (i, j)
                row.append(sample_uniform_poly(rho, ii, jj, KYBER_N, KYBER_Q))
            mat.append(row)
        return mat

    def keygen(self, seed: bytes | None = None) -> Tuple[bytes, bytes]:
        """Generate (public_key, secret_key)."""
        if seed is None:
            seed = secrets.token_bytes(64)
        elif len(seed) != 64:
            seed = hashlib.shake_256(seed).digest(64)

        d = seed[:32]
        z = seed[32:64]
        
        # Expand d into public seed rho and secret noise seed sigma
        g_out = sha3_512(d)
        rho, sigma = g_out[:32], g_out[32:64]

        # Generate matrix A
        A = self._sample_matrix(rho)

        # Sample secret vector s and error vector e
        s = [sample_cbd(sigma + bytes([i]), self.eta1, KYBER_N, KYBER_Q) for i in range(self.k)]
        e = [sample_cbd(sigma + bytes([self.k + i]), self.eta1, KYBER_N, KYBER_Q) for i in range(self.k)]

        # Compute public vector t = A * s + e
        t = []
        for i in range(self.k):
            row_sum = Poly([0] * KYBER_N, KYBER_N, KYBER_Q)
            for j in range(self.k):
                row_sum = row_sum + (A[i][j] * s[j])
            t.append(row_sum + e[i])

        # Pack public key: t bytes + rho
        pk = b"".join(poly.to_bytes() for poly in t) + rho
        
        # Pack secret key: s bytes + pk + H(pk) + z
        hpk = sha3_256(pk)
        sk = b"".join(poly.to_bytes() for poly in s) + pk + hpk + z
        return pk, sk

    def encapsulate(self, pk: bytes, seed: bytes | None = None) -> Tuple[bytes, bytes]:
        """Encapsulate shared secret against public key pk.
        
        Returns (ciphertext, shared_secret_32_bytes).
        """
        if seed is None:
            m = secrets.token_bytes(32)
        else:
            m = seed[:32]

        # Unpack public key
        poly_bytes_len = (KYBER_N * 12) // 8
        t = []
        offset = 0
        for _ in range(self.k):
            t.append(Poly.from_bytes(pk[offset:offset + poly_bytes_len], KYBER_N, KYBER_Q))
            offset += poly_bytes_len
        rho = pk[offset:offset + 32]

        # Hash m and pk
        hpk = sha3_256(pk)
        g_out = sha3_512(m + hpk)
        kr, r_seed = g_out[:32], g_out[32:64]

        # Generate transposed matrix A^T
        AT = self._sample_matrix(rho, transpose=True)

        # Sample randomness vectors r, e1, and error scalar e2
        r_vec = [sample_cbd(r_seed + bytes([i]), self.eta1, KYBER_N, KYBER_Q) for i in range(self.k)]
        e1 = [sample_cbd(r_seed + bytes([self.k + i]), self.eta2, KYBER_N, KYBER_Q) for i in range(self.k)]
        e2 = sample_cbd(r_seed + bytes([2 * self.k]), self.eta2, KYBER_N, KYBER_Q)

        # Compute u = A^T * r + e1
        u = []
        for i in range(self.k):
            row_sum = Poly([0] * KYBER_N, KYBER_N, KYBER_Q)
            for j in range(self.k):
                row_sum = row_sum + (AT[i][j] * r_vec[j])
            u.append(row_sum + e1[i])

        # Compute v = t^T * r + e2 + encode(m)
        v_sum = Poly([0] * KYBER_N, KYBER_N, KYBER_Q)
        for i in range(self.k):
            v_sum = v_sum + (t[i] * r_vec[i])
        m_poly = encode_message_to_poly(m)
        v = v_sum + e2 + m_poly

        # Pack ciphertext
        c_u = b"".join(poly.to_bytes() for poly in u)
        c_v = v.to_bytes()
        ciphertext = c_u + c_v

        # Final shared secret derivation: KDF(kr || H(c))
        shared_secret = sha3_256(kr + sha3_256(ciphertext))
        return ciphertext, shared_secret

    def decapsulate(self, sk: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate ciphertext with secret key sk.
        
        Returns shared_secret_32_bytes (using Fujisaki-Okamoto verification).
        """
        poly_bytes_len = (KYBER_N * 12) // 8
        
        # Unpack secret key: s (k polys) + pk + hpk + z
        s = []
        offset = 0
        for _ in range(self.k):
            s.append(Poly.from_bytes(sk[offset:offset + poly_bytes_len], KYBER_N, KYBER_Q))
            offset += poly_bytes_len

        pk_len = (self.k * poly_bytes_len) + 32
        pk = sk[offset:offset + pk_len]
        offset += pk_len
        hpk = sk[offset:offset + 32]
        offset += 32
        z = sk[offset:offset + 32]

        # Unpack ciphertext: u (k polys) + v (1 poly)
        u = []
        c_offset = 0
        for _ in range(self.k):
            u.append(Poly.from_bytes(ciphertext[c_offset:c_offset + poly_bytes_len], KYBER_N, KYBER_Q))
            c_offset += poly_bytes_len
        v = Poly.from_bytes(ciphertext[c_offset:c_offset + poly_bytes_len], KYBER_N, KYBER_Q)

        # Compute m' = decode(v - s^T * u)
        s_dot_u = Poly([0] * KYBER_N, KYBER_N, KYBER_Q)
        for i in range(self.k):
            s_dot_u = s_dot_u + (s[i] * u[i])
        m_noisy = v - s_dot_u
        m_prime = decode_poly_to_message(m_noisy)

        # Re-encrypt m' under pk to verify ciphertext integrity
        g_out = sha3_512(m_prime + hpk)
        kr_prime, r_seed_prime = g_out[:32], g_out[32:64]

        # Check ciphertext validity (Fujisaki-Okamoto transform)
        recomputed_c, expected_ss = self.encapsulate(pk, seed=m_prime)
        
        if secrets.compare_digest(recomputed_c, ciphertext):
            # Ciphertext matches: return valid shared secret
            return sha3_256(kr_prime + sha3_256(ciphertext))
        else:
            # Ciphertext tampering detected: implicit rejection with pseudorandom secret z
            return sha3_256(z + sha3_256(ciphertext))


# Preconfigured instances
ml_kem_512 = MLKEM(PARAMS_512)
ml_kem_768 = MLKEM(PARAMS_768)
ml_kem_1024 = MLKEM(PARAMS_1024)
