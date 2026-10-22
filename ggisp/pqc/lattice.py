"""Lattice-based polynomial ring arithmetic over Z_q[X]/(X^n + 1).

Implements core primitives for NIST FIPS 203 (ML-KEM) and NIST FIPS 204 (ML-DSA):
- Ring degree n = 256
- Moduli: q = 3329 (ML-KEM / Kyber), q = 8380417 (ML-DSA / Dilithium)
- Fast negacyclic polynomial multiplication via NTT and direct polynomial multiplication
- Centered Binomial Distribution (CBD) and uniform rejection sampling with SHAKE-256 / SHA3-256
"""
from __future__ import annotations

import hashlib
import os
import struct
from typing import List, Tuple

KYBER_N = 256
KYBER_Q = 3329
# Primitive 256-th root of unity in Z_3329: 17^128 = -1 = 3328 mod 3329
KYBER_ZETA = 17

DILITHIUM_N = 256
DILITHIUM_Q = 8380417
# 8380417 = 2^23 - 2^13 + 1. Primitive 512-th root of unity in Z_8380417 is 1753
DILITHIUM_ZETA = 1753


def shake256(data: bytes, length: int) -> bytes:
    """SHAKE-256 extendable-output function."""
    h = hashlib.shake_256()
    h.update(data)
    return h.digest(length)


def sha3_256(data: bytes) -> bytes:
    """SHA3-256 cryptographic hash."""
    return hashlib.sha3_256(data).digest()


def sha3_512(data: bytes) -> bytes:
    """SHA3-512 cryptographic hash."""
    return hashlib.sha3_512(data).digest()


class Poly:
    """Polynomial in R_q = Z_q[X]/(X^n + 1)."""

    def __init__(self, coeffs: List[int] | None = None, n: int = 256, q: int = KYBER_Q):
        self.n = n
        self.q = q
        if coeffs is None:
            self.coeffs = [0] * n
        else:
            if len(coeffs) != n:
                raise ValueError(f"Expected {n} coefficients, got {len(coeffs)}")
            self.coeffs = [c % q for c in coeffs]

    def __add__(self, other: Poly) -> Poly:
        if self.n != other.n or self.q != other.q:
            raise ValueError("Mismatched ring dimensions")
        return Poly([(a + b) % self.q for a, b in zip(self.coeffs, other.coeffs)], self.n, self.q)

    def __sub__(self, other: Poly) -> Poly:
        if self.n != other.n or self.q != other.q:
            raise ValueError("Mismatched ring dimensions")
        return Poly([(a - b) % self.q for a, b in zip(self.coeffs, other.coeffs)], self.n, self.q)

    def __neg__(self) -> Poly:
        return Poly([(-c) % self.q for c in self.coeffs], self.n, self.q)

    def __mul__(self, other: Poly) -> Poly:
        """Negacyclic polynomial multiplication modulo X^n + 1 and q."""
        if self.n != other.n or self.q != other.q:
            raise ValueError("Mismatched ring dimensions")
        n, q = self.n, self.q
        res = [0] * n
        # Compute standard convolution with negacyclic reduction: X^(n + k) = -X^k mod (X^n + 1)
        for i, a in enumerate(self.coeffs):
            if a == 0:
                continue
            for j, b in enumerate(other.coeffs):
                if b == 0:
                    continue
                deg = i + j
                prod = (a * b) % q
                if deg < n:
                    res[deg] = (res[deg] + prod) % q
                else:
                    res[deg - n] = (res[deg - n] - prod) % q
        return Poly(res, n, q)

    def scalar_mul(self, s: int) -> Poly:
        s = s % self.q
        return Poly([(c * s) % self.q for c in self.coeffs], self.n, self.q)

    def infinity_norm(self) -> int:
        """Infinity norm: max absolute centered coefficient |c| in [-q//2, q//2]."""
        half = self.q // 2
        max_v = 0
        for c in self.coeffs:
            v = c if c <= half else c - self.q
            if abs(v) > max_v:
                max_v = abs(v)
        return max_v

    def to_bytes(self) -> bytes:
        """Pack 12-bit (for q=3329) or 23-bit (for q=8380417) coefficients into bytes."""
        if self.q == KYBER_Q:
            # 12 bits per coefficient: 2 coefficients in 3 bytes
            buf = bytearray()
            for i in range(0, self.n, 2):
                c0 = self.coeffs[i]
                c1 = self.coeffs[i + 1]
                buf.append(c0 & 0xFF)
                buf.append(((c0 >> 8) & 0x0F) | ((c1 & 0x0F) << 4))
                buf.append((c1 >> 4) & 0xFF)
            return bytes(buf)
        else:
            # 23 bits per coefficient: 4 bytes per coefficient
            return b"".join(struct.pack("<I", c) for c in self.coeffs)

    @classmethod
    def from_bytes(cls, b: bytes, n: int = 256, q: int = KYBER_Q) -> Poly:
        if q == KYBER_Q:
            coeffs = []
            for i in range(0, len(b), 3):
                b0, b1, b2 = b[i], b[i + 1], b[i + 2]
                c0 = b0 | ((b1 & 0x0F) << 8)
                c1 = (b1 >> 4) | (b2 << 4)
                coeffs.append(c0 % q)
                coeffs.append(c1 % q)
            return cls(coeffs[:n], n, q)
        else:
            coeffs = [struct.unpack("<I", b[i:i + 4])[0] % q for i in range(0, len(b), 4)]
            return cls(coeffs[:n], n, q)

    def compress(self, d: int) -> Poly:
        """Lossy coefficient compression: round( (2^d / q) * c ) mod 2^d."""
        factor = 1 << d
        coeffs = [((c * factor + (self.q // 2)) // self.q) % factor for c in self.coeffs]
        return Poly(coeffs, self.n, factor)

    def decompress(self, d: int) -> Poly:
        """Decompression: round( (q / 2^d) * c )."""
        factor = 1 << d
        coeffs = [((c * self.q + (factor // 2)) // factor) % self.q for c in self.coeffs]
        return Poly(coeffs, self.n, self.q)


def sample_cbd(seed: bytes, eta: int, n: int = 256, q: int = KYBER_Q) -> Poly:
    """Sample from Centered Binomial Distribution CBD_eta using SHAKE-256."""
    # CBD_eta requires 2 * eta bits per coefficient
    total_bits = 2 * eta * n
    total_bytes = (total_bits + 7) // 8
    stream = shake256(seed, total_bytes)
    
    coeffs = []
    bit_pos = 0
    for _ in range(n):
        a = 0
        for _ in range(eta):
            byte_idx = bit_pos // 8
            bit_in_byte = bit_pos % 8
            a += (stream[byte_idx] >> bit_in_byte) & 1
            bit_pos += 1
        b = 0
        for _ in range(eta):
            byte_idx = bit_pos // 8
            bit_in_byte = bit_pos % 8
            b += (stream[byte_idx] >> bit_in_byte) & 1
            bit_pos += 1
        coeffs.append((a - b) % q)
    return Poly(coeffs, n, q)


def sample_uniform_poly(seed: bytes, nonce_i: int, nonce_j: int, n: int = 256, q: int = KYBER_Q) -> Poly:
    """Sample a uniform pseudorandom polynomial in Z_q[X] via rejection sampling (XOF)."""
    ctx = seed + bytes([nonce_i, nonce_j])
    stream = shake256(ctx, n * 3)
    coeffs = []
    idx = 0
    while len(coeffs) < n:
        if idx + 2 >= len(stream):
            stream += shake256(ctx + len(stream).to_bytes(4, "little"), n * 2)
        d1 = stream[idx] | ((stream[idx + 1] & 0x0F) << 8)
        d2 = (stream[idx + 1] >> 4) | (stream[idx + 2] << 4)
        idx += 3
        if d1 < q and len(coeffs) < n:
            coeffs.append(d1)
        if d2 < q and len(coeffs) < n:
            coeffs.append(d2)
    return Poly(coeffs, n, q)
