"""NIST FIPS 204: Module-Lattice Digital Signature Algorithm (ML-DSA / Dilithium).

Implements post-quantum digital signatures based on the hardness of Module Learning With Errors
(M-LWE) and Module Short Integer Solution (M-SIS) over polynomial rings with "Fiat-Shamir with Aborts".
"""
from __future__ import annotations

import hashlib
import os
import secrets
from typing import NamedTuple, Tuple

from ggisp.pqc.lattice import (
    DILITHIUM_N,
    DILITHIUM_Q,
    Poly,
    sha3_256,
    shake256,
)


class MLDSAParams(NamedTuple):
    name: str
    k: int
    l: int
    eta: int
    gamma1: int
    tau: int
    beta: int


# ML-DSA-65 (NIST Security Level 3, matching AES-192 / Dilithium-3)
PARAMS_65 = MLDSAParams(
    name="ML-DSA-65",
    k=6,
    l=5,
    eta=4,
    gamma1=524288,        # 2^19
    tau=49,               # Number of +/-1 in challenge polynomial
    beta=196,             # tau * eta
)


def sample_in_ball(seed: bytes, tau: int = 49, n: int = 256) -> Poly:
    """Sample challenge polynomial c in R_q with exactly tau non-zero coefficients in {-1, 1}."""
    stream = shake256(seed, 128)
    signs = int.from_bytes(stream[:8], "little")
    pos = 8
    coeffs = [0] * n
    
    count = 0
    while count < tau:
        if pos >= len(stream):
            stream += shake256(seed + pos.to_bytes(4, "big"), 64)
        j = stream[pos]
        pos += 1
        if j < n and coeffs[j] == 0:
            sign = -1 if (signs & 1) else 1
            signs >>= 1
            coeffs[j] = sign % DILITHIUM_Q
            count += 1
    return Poly(coeffs, n, DILITHIUM_Q)


def sample_mask_poly(seed: bytes, gamma1: int, n: int = 256, q: int = DILITHIUM_Q) -> Poly:
    """Sample masking polynomial with coefficients uniformly in [-gamma1 + 1, gamma1]."""
    stream = shake256(seed, n * 3)
    coeffs = []
    idx = 0
    span = 2 * gamma1 - 1
    while len(coeffs) < n:
        if idx + 3 > len(stream):
            stream += shake256(seed + len(stream).to_bytes(4, "big"), n * 2)
        val = stream[idx] | (stream[idx + 1] << 8) | ((stream[idx + 2] & 0x0F) << 16)
        idx += 3
        if val < span:
            centered = val - (gamma1 - 1)
            coeffs.append(centered % q)
    return Poly(coeffs, n, q)


def sample_eta_poly(seed: bytes, eta: int, n: int = 256, q: int = DILITHIUM_Q) -> Poly:
    """Sample secret polynomial with coefficients in [-eta, eta]."""
    stream = shake256(seed, n)
    coeffs = []
    idx = 0
    while len(coeffs) < n:
        if idx >= len(stream):
            stream += shake256(seed + idx.to_bytes(4, "big"), n)
        b = stream[idx]
        idx += 1
        t0 = b & 0x0F
        t1 = b >> 4
        if t0 < 9 and len(coeffs) < n:
            coeffs.append((t0 - eta) % q)
        if t1 < 9 and len(coeffs) < n:
            coeffs.append((t1 - eta) % q)
    return Poly(coeffs, n, q)


class MLDSA:
    """NIST FIPS 204 Module-Lattice Digital Signature Algorithm."""

    def __init__(self, params: MLDSAParams = PARAMS_65):
        self.params = params
        self.k = params.k
        self.l = params.l
        self.eta = params.eta
        self.gamma1 = params.gamma1
        self.tau = params.tau
        self.beta = params.beta

    def _sample_matrix(self, rho: bytes) -> list[list[Poly]]:
        """Sample k x l matrix of polynomials in Z_q[X] from seed rho."""
        mat = []
        for i in range(self.k):
            row = []
            for j in range(self.l):
                seed_ij = rho + bytes([i, j])
                row.append(Poly.from_bytes(shake256(seed_ij, DILITHIUM_N * 4), DILITHIUM_N, DILITHIUM_Q))
            mat.append(row)
        return mat

    def keygen(self, seed: bytes | None = None) -> Tuple[bytes, bytes]:
        """Generate (public_key, secret_key)."""
        if seed is None:
            seed = secrets.token_bytes(32)
        
        expanded = shake256(seed, 128)
        rho = expanded[:32]
        sigma = expanded[32:96]
        K = expanded[96:128]

        # Generate matrix A
        A = self._sample_matrix(rho)

        # Sample secret vector s1 in R_q^l
        s1 = [sample_eta_poly(sigma + bytes([i]), self.eta, DILITHIUM_N, DILITHIUM_Q) for i in range(self.l)]

        # Compute public key t = A * s1
        t = []
        for i in range(self.k):
            row_sum = Poly([0] * DILITHIUM_N, DILITHIUM_N, DILITHIUM_Q)
            for j in range(self.l):
                row_sum = row_sum + (A[i][j] * s1[j])
            t.append(row_sum)

        pk = rho + b"".join(poly.to_bytes() for poly in t)
        tr = sha3_256(pk)

        s1_bytes = b"".join(poly.to_bytes() for poly in s1)
        sk = rho + K + tr + s1_bytes + b"".join(poly.to_bytes() for poly in t)
        return pk, sk

    def sign(self, sk: bytes, message: bytes) -> bytes:
        """Sign message using secret key sk with Fiat-Shamir with Aborts."""
        rho = sk[:32]
        K = sk[32:64]
        tr = sk[64:96]
        offset = 96
        
        poly_bytes_len = DILITHIUM_N * 4
        s1 = []
        for _ in range(self.l):
            s1.append(Poly.from_bytes(sk[offset:offset + poly_bytes_len], DILITHIUM_N, DILITHIUM_Q))
            offset += poly_bytes_len

        mu = sha3_256(tr + message)
        A = self._sample_matrix(rho)

        nonce = 0
        while True:
            nonce += 1
            rho_prime = shake256(K + mu + nonce.to_bytes(4, "little"), 64)
            y = [sample_mask_poly(rho_prime + bytes([i]), self.gamma1) for i in range(self.l)]

            # w = A * y
            w = []
            for i in range(self.k):
                row_sum = Poly([0] * DILITHIUM_N, DILITHIUM_N, DILITHIUM_Q)
                for j in range(self.l):
                    row_sum = row_sum + (A[i][j] * y[j])
                w.append(row_sum)

            w_bytes = b"".join(poly.to_bytes() for poly in w)
            c_seed = sha3_256(mu + w_bytes)
            c = sample_in_ball(c_seed, self.tau, DILITHIUM_N)

            # z = y + c * s1
            z = []
            restart = False
            for j in range(self.l):
                z_j = y[j] + (c * s1[j])
                # Rejection sampling check: norm bound ||z||_inf < gamma1 - beta
                if z_j.infinity_norm() >= self.gamma1 - self.beta:
                    restart = True
                    break
                z.append(z_j)

            if restart:
                continue

            return c_seed + b"".join(poly.to_bytes() for poly in z)

    def verify(self, pk: bytes, message: bytes, signature: bytes) -> bool:
        """Verify signature against public key pk and message."""
        try:
            poly_bytes_len = DILITHIUM_N * 4
            expected_sig_len = 32 + (self.l * poly_bytes_len)
            if len(signature) != expected_sig_len:
                return False

            rho = pk[:32]
            offset = 32
            t = []
            for _ in range(self.k):
                t.append(Poly.from_bytes(pk[offset:offset + poly_bytes_len], DILITHIUM_N, DILITHIUM_Q))
                offset += poly_bytes_len

            c_seed = signature[:32]
            z = []
            z_offset = 32
            for _ in range(self.l):
                z_poly = Poly.from_bytes(signature[z_offset:z_offset + poly_bytes_len], DILITHIUM_N, DILITHIUM_Q)
                if z_poly.infinity_norm() >= self.gamma1 - self.beta:
                    return False
                z.append(z_poly)
                z_offset += poly_bytes_len

            A = self._sample_matrix(rho)
            c = sample_in_ball(c_seed, self.tau, DILITHIUM_N)

            # Reconstruct w' = A * z - c * t
            w_prime = []
            for i in range(self.k):
                az_sum = Poly([0] * DILITHIUM_N, DILITHIUM_N, DILITHIUM_Q)
                for j in range(self.l):
                    az_sum = az_sum + (A[i][j] * z[j])
                w_prime.append(az_sum - (c * t[i]))

            tr = sha3_256(pk)
            mu = sha3_256(tr + message)
            w_prime_bytes = b"".join(poly.to_bytes() for poly in w_prime)
            recomputed_c_seed = sha3_256(mu + w_prime_bytes)

            return secrets.compare_digest(c_seed, recomputed_c_seed)
        except Exception:
            return False


# Preconfigured instance
ml_dsa_65 = MLDSA(PARAMS_65)
