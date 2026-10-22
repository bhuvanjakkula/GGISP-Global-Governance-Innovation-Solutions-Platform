"""GGISP Cryptographic Evidence & Compute Merkle Tree Engine.
Generates deterministic, tamper-proof Merkle proofs for policy decisions, simulation results, and empirical evidence.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any, Dict, List, Tuple
from ggisp.db import db


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hash_record(record_type: str, payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(f"{record_type}:{serialized}")


def build_merkle_tree(leaf_hashes: List[str]) -> Dict[str, Any]:
    """Build a complete binary Merkle tree from a list of leaf hashes."""
    if not leaf_hashes:
        empty_root = sha256("EMPTY_TREE")
        return {"root": empty_root, "layers": [[empty_root]], "leaf_count": 0}

    layers: List[List[str]] = [leaf_hashes]
    current_layer = leaf_hashes

    while len(current_layer) > 1:
        next_layer: List[str] = []
        for i in range(0, len(current_layer), 2):
            left = current_layer[i]
            # Duplicate the last node if odd count
            right = current_layer[i + 1] if i + 1 < len(current_layer) else left
            parent = sha256(left + right)
            next_layer.append(parent)
        layers.append(next_layer)
        current_layer = next_layer

    return {
        "root": current_layer[0],
        "layers": layers,
        "leaf_count": len(leaf_hashes)
    }


def generate_merkle_proof(tree: Dict[str, Any], leaf_index: int) -> Dict[str, Any]:
    """Extract the cryptographic proof path for a specific leaf index."""
    layers = tree["layers"]
    proof = []
    idx = leaf_index

    for layer in layers[:-1]:
        is_right = (idx % 2 == 1)
        sibling_idx = idx - 1 if is_right else idx + 1
        if sibling_idx < len(layer):
            sibling_hash = layer[sibling_idx]
        else:
            sibling_hash = layer[idx]

        proof.append({
            "position": "left" if is_right else "right",
            "sibling_hash": sibling_hash
        })
        idx = idx // 2

    return {
        "leaf_index": leaf_index,
        "leaf_hash": layers[0][leaf_index],
        "root": tree["root"],
        "proof_steps": proof
    }


def verify_merkle_proof(root: str, leaf_hash: str, proof: List[Dict[str, str]]) -> bool:
    """Verify that a given leaf hash belongs to the Merkle tree with the specified root."""
    current = leaf_hash
    for step in proof:
        sibling = step["sibling_hash"]
        pos = step["position"]
        if pos == "left":
            current = sha256(sibling + current)
        else:
            current = sha256(current + sibling)
    return current == root


def generate_planetary_audit_tree() -> Dict[str, Any]:
    """Audit all active projects, approved recommendations, and verified evidence into a live Merkle Root."""
    with db() as con:
        projects = con.execute("SELECT id, domain_slug, title, problem, country_code FROM projects").fetchall()
        sources = con.execute("SELECT id, title, publisher, url, quality_rating FROM sources").fetchall()
        recs = con.execute("SELECT id, project_id, recommendation, approval_status, author FROM recommendations").fetchall()
        sims = con.execute("SELECT id, project_id, model_type, scenario_name FROM simulations").fetchall()

    leaves = []
    metadata_index = []

    for p in projects:
        h = hash_record("PROJECT", dict(p))
        leaves.append(h)
        metadata_index.append({"type": "project", "id": p["id"], "title": p["title"], "hash": h})

    for s in sources:
        h = hash_record("SOURCE", dict(s))
        leaves.append(h)
        metadata_index.append({"type": "source", "id": s["id"], "title": s["title"], "hash": h})

    for r in recs:
        h = hash_record("RECOMMENDATION", dict(r))
        leaves.append(h)
        metadata_index.append({"type": "recommendation", "id": r["id"], "title": r["recommendation"][:40], "hash": h})

    for sm in sims:
        h = hash_record("SIMULATION", dict(sm))
        leaves.append(h)
        metadata_index.append({"type": "simulation", "id": sm["id"], "title": sm["scenario_name"], "hash": h})

    if not leaves:
        leaves.append(sha256("GENESIS_BLOCK_GGISP_2026"))
        metadata_index.append({"type": "genesis", "id": 0, "title": "GGISP Genesis", "hash": leaves[0]})

    tree = build_merkle_tree(leaves)
    return {
        "merkle_root": tree["root"],
        "total_attested_records": tree["leaf_count"],
        "layers_depth": len(tree["layers"]),
        "verified_leaves": metadata_index,
        "tree_internal": tree
    }
