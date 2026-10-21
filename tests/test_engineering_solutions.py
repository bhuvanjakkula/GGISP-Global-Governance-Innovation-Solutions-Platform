"""Tests for GGISP Planetary Engineering Technologies & Operational Solvers."""
import pytest
from fastapi.testclient import TestClient
from ggisp.main import app
from ggisp.engineering.merkle import (
    build_merkle_tree,
    generate_merkle_proof,
    verify_merkle_proof,
    generate_planetary_audit_tree,
)
from ggisp.engineering.cascade_solver import CascadeShockInput, solve_planetary_cascade
from ggisp.engineering.playbooks import (
    generate_space_conjunction_cdm,
    generate_mocc_health_fhir_dispatch,
    generate_stix_cyber_threat_bundle,
    generate_critical_minerals_geojson,
    generate_parametric_climate_smart_contract,
    generate_sovereign_cac_voting_script,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_merkle_tree_cryptographic_verification():
    leaves = [
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
        "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
        "2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6"
    ]
    tree = build_merkle_tree(leaves)
    assert tree["leaf_count"] == 4
    assert len(tree["root"]) == 64

    # Test proof verification for leaf 2
    proof_info = generate_merkle_proof(tree, 2)
    assert proof_info["leaf_hash"] == leaves[2]
    is_valid = verify_merkle_proof(tree["root"], leaves[2], proof_info["proof_steps"])
    assert is_valid is True

    # Test tampering detection
    is_tampered_valid = verify_merkle_proof(tree["root"], "tampered_fake_hash", proof_info["proof_steps"])
    assert is_tampered_valid is False


def test_planetary_audit_tree_generation():
    audit_tree = generate_planetary_audit_tree()
    assert "merkle_root" in audit_tree
    assert len(audit_tree["merkle_root"]) == 64
    assert audit_tree["total_attested_records"] >= 1


def test_systemic_cascade_solver():
    res = solve_planetary_cascade(CascadeShockInput(
        climate_cyclone_intensity_knots=135.0,
        sovereign_debt_gdp_percent=95.0,
        icu_pandemic_surge_r0=3.8,
        space_debris_conjunction_p_c=5.2e-4,
        critical_mineral_embargo_percent=45.0,
        available_emergency_fiscal_buffer_million_usd=300.0
    ))
    assert res["pre_intervention_systemic_vulnerability_index_100"] > 50.0
    assert res["post_intervention_residual_vulnerability_100"] < res["pre_intervention_systemic_vulnerability_index_100"]
    assert res["cascade_suppression_efficiency_percent"] > 25.0
    assert len(res["cross_domain_feedback_loops"]) == 3
    assert len(res["pareto_optimal_resource_dispatch"]["allocations"]) == 4


def test_engineering_playbook_generators():
    cdm = generate_space_conjunction_cdm(45.0, 2.4e-4, 550.0)
    assert cdm["standard"] == "CCSDS 508.0-B-1 (Conjunction Data Message)"
    assert cdm["operational_burn_command"]["execution_status"] == "MANDATORY_EXECUTION"

    fhir = generate_mocc_health_fhir_dispatch(32, 75.0, 8.9)
    assert fhir["resourceType"] == "Bundle"
    assert len(fhir["clinical_transfer_requests"]) > 0

    stix = generate_stix_cyber_threat_bundle()
    assert stix["type"] == "bundle"

    geojson = generate_critical_minerals_geojson()
    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"][0]["geometry"]["type"] == "Polygon"

    evm = generate_parametric_climate_smart_contract()
    assert "0x" in evm["contract_address"]

    cac = generate_sovereign_cac_voting_script()
    assert cac["aggregate_voting_threshold_percent"] == 75.0


def test_api_engineering_endpoints(client):
    # Test playbook retrieval
    r_space = client.get("/api/engineering/playbooks/space-security")
    assert r_space.status_code == 200
    assert r_space.json()["standard"] == "CCSDS 508.0-B-1 (Conjunction Data Message)"

    r_health = client.get("/api/engineering/playbooks/global-health")
    assert r_health.status_code == 200
    assert r_health.json()["resourceType"] == "Bundle"

    # Test Merkle audit
    r_audit = client.get("/api/engineering/merkle/audit-tree")
    assert r_audit.status_code == 200
    data = r_audit.json()
    root = data["merkle_root"]
    assert len(root) == 64

    # Test proof verification endpoint
    tree = data["tree_internal"]
    proof = generate_merkle_proof(tree, 0)
    r_verify = client.post("/api/engineering/merkle/verify-proof", json={
        "root": root,
        "leaf_hash": proof["leaf_hash"],
        "proof_steps": proof["proof_steps"]
    })
    assert r_verify.status_code == 200
    assert r_verify.json()["verified"] is True

    # Test cascade solver endpoint
    r_cascade = client.post("/api/engineering/cascade/simulate", json={
        "climate_cyclone_intensity_knots": 115.0,
        "sovereign_debt_gdp_percent": 80.0,
        "icu_pandemic_surge_r0": 2.5,
        "space_debris_conjunction_p_c": 1.2e-4,
        "critical_mineral_embargo_percent": 20.0,
        "available_emergency_fiscal_buffer_million_usd": 200.0
    })
    assert r_cascade.status_code == 200
    assert "pre_intervention_systemic_vulnerability_index_100" in r_cascade.json()
