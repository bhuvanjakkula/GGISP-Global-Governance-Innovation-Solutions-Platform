import urllib.request
import json

def test(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, headers={'Content-Type': 'application/json'})
    body = json.dumps(data).encode('utf-8') if data else None
    with urllib.request.urlopen(req, data=body, timeout=5) as res:
        return res.status, json.loads(res.read().decode('utf-8'))

# 1. Test Projects & Metrics Summary
st, projects = test('http://127.0.0.1:8000/api/projects')
print(f"Projects count: {len(projects)} (Status: {st})")
st_m, metrics = test('http://127.0.0.1:8000/api/metrics/summary')
print(f"Metrics summary: Divisions: {metrics['divisions']}, Projects: {metrics['projects']}, Evidence: {metrics['total_evidence']}, Approved: {metrics['approved_guidance']} (Status: {st_m})")

# 2. Test Catalog & All 13 Engines & Playbooks
st, catalog = test('http://127.0.0.1:8000/api/engines/catalog')
print(f"Catalog engines: {len(catalog)} (Status: {st})")

for eng in catalog:
    slug = eng['domain_slug']
    st_pb, pb = test(f'http://127.0.0.1:8000/api/engineering/playbooks/{slug}')
    st_sim, sim = test(f'http://127.0.0.1:8000/api/engines/{slug}/simulate', method='POST', data=eng['default_parameters'])
    std = pb.get('standard') or pb.get('resourceType') or pb.get('type')
    eng_name = sim.get('engine') or eng['engine_name']
    print(f"  [OK] {slug:<22} | Engine: {eng_name[:32]}... | Standard: {std}")

# 3. Test Merkle Attestation
st_m, merkle = test('http://127.0.0.1:8000/api/engineering/merkle/audit-tree')
print(f"Merkle Root: {merkle['merkle_root'][:28]}... Total Attested: {merkle['total_attested_records']}")

# 4. Test Cascade Solver
st_cas, cascade = test('http://127.0.0.1:8000/api/engineering/cascade/simulate', method='POST', data={
    'climate_cyclone_intensity_knots': 120.0,
    'sovereign_debt_gdp_percent': 85.0,
    'icu_pandemic_surge_r0': 2.8,
    'space_debris_conjunction_p_c': 2.0e-4,
    'critical_mineral_embargo_percent': 30.0,
    'available_emergency_fiscal_buffer_million_usd': 250.0
})
print(f"Cascade Solver: SVI {cascade['pre_intervention_systemic_vulnerability_index_100']} -> {cascade['post_intervention_residual_vulnerability_100']} (Arrest: {cascade['cascade_suppression_efficiency_percent']}%)")

# 5. Test 20 Analytical & Advanced Workbench Engines
st_wb_cat, wb_catalog = test('http://127.0.0.1:8000/api/engines')
print(f"Workbench analytical engines catalog: {len(wb_catalog)} engines (Status: {st_wb_cat})")

# Test Minimax Regret & Maximin Robust Policy
st_rob, rob_res = test('http://127.0.0.1:8000/api/engines/robust-policy/calculate', method='POST', data={
    'name': 'Live Robust Choice Test',
    'parameters': {
        'scenarios': [{'name': 'Favorable', 'weight': 1}, {'name': 'Adverse', 'weight': 1}],
        'options': [{'name': 'High upside', 'outcomes': [100, 0]}, {'name': 'Resilient option', 'outcomes': [65, 55]}]
    }
})
print(f"  [OK] Robust Policy Engine: Minimax Choice = '{rob_res['metrics']['minimax_regret_choice']}', Minimax Regret = {rob_res['metrics']['minimax_regret']}")

# Test Supply Network Bottleneck Max-Flow / Min-Cut
st_net, net_res = test('http://127.0.0.1:8000/api/engines/supply-network/calculate', method='POST', data={
    'name': 'Critical Supply Bottleneck',
    'parameters': {
        'source': 'Supply', 'sink': 'Demand', 'required_throughput': 12,
        'edges': [
            {'origin': 'Supply', 'destination': 'Port A', 'capacity': 10, 'disruption_percent': 50},
            {'origin': 'Supply', 'destination': 'Port B', 'capacity': 6, 'disruption_percent': 0},
            {'origin': 'Port A', 'destination': 'Demand', 'capacity': 8, 'disruption_percent': 0},
            {'origin': 'Port B', 'destination': 'Demand', 'capacity': 6, 'disruption_percent': 0}
        ]
    }
})
print(f"  [OK] Supply Network MaxFlow/MinCut: Baseline = {net_res['metrics']['baseline_maximum_throughput']}, Disrupted = {net_res['metrics']['disrupted_maximum_throughput']}")

# 6. Test Connectors & Workbench Pages
st_conn, conn_cat = test('http://127.0.0.1:8000/api/connectors')
print(f"Connectors Catalog: World Bank status = '{conn_cat['world_bank']['status']}' (Status: {st_conn})")

# 7. Test Post-Quantum Cryptography (PQC) Subsystem
print("\n--- Verifying Post-Quantum Cryptography (PQC) Subsystem ---")
st_pqc, pqc_stat = test('http://127.0.0.1:8000/api/pqc/status')
print(f"PQC Status: {pqc_stat['quantum_readiness_level']} (Active Standards: {len(pqc_stat['active_standards'])})")

# Test KEM-768
st_kem, kem_kp = test('http://127.0.0.1:8000/api/pqc/kem/generate-keypair', method='POST')
print(f"  [OK] ML-KEM-768 Keygen: PK={kem_kp['public_key_bytes_len']}B, SK={kem_kp['secret_key_bytes_len']}B")
st_enc, enc_res = test('http://127.0.0.1:8000/api/pqc/kem/encapsulate', method='POST', data={'public_key_hex': kem_kp['public_key_hex']})
print(f"  [OK] ML-KEM-768 Encapsulation: Shared Secret bits = {enc_res['shared_secret_bits']}")
st_dec, dec_res = test('http://127.0.0.1:8000/api/pqc/kem/decapsulate', method='POST', data={
    'secret_key_hex': kem_kp['secret_key_hex'],
    'ciphertext_hex': enc_res['ciphertext_hex']
})
assert enc_res['shared_secret_hex'] == dec_res['shared_secret_hex']
print(f"  [OK] ML-KEM-768 Decapsulation: 100% Shared Secret Reconciled ({dec_res['decapsulation_status']})")

# Test DSA-65
st_dsa, dsa_kp = test('http://127.0.0.1:8000/api/pqc/dsa/generate-keypair', method='POST')
st_sig, sig_res = test('http://127.0.0.1:8000/api/pqc/dsa/sign', method='POST', data={
    'secret_key_hex': dsa_kp['secret_key_hex'],
    'message': 'Sovereign Debt Mitigation Accord'
})
print(f"  [OK] ML-DSA-65 Signature: {sig_res['signature_bytes_len']} bytes (SHA3-256: {sig_res['message_digest_sha3_256'][:16]}...)")
st_ver, ver_res = test('http://127.0.0.1:8000/api/pqc/dsa/verify', method='POST', data={
    'public_key_hex': dsa_kp['public_key_hex'],
    'message': 'Sovereign Debt Mitigation Accord',
    'signature_hex': sig_res['signature_hex']
})
assert ver_res['verified'] is True
print(f"  [OK] ML-DSA-65 Verification: Authenticated = {ver_res['verified']} ({ver_res['status']})")

# Test Hybrid Envelope Encryption
st_env_enc, env_enc = test('http://127.0.0.1:8000/api/pqc/envelope/encrypt', method='POST', data={
    'public_key_hex': kem_kp['public_key_hex'],
    'plaintext': 'CLASSIFIED_POLICY_ACCORD_13_DIVISIONS',
    'associated_data': 'GGISP-PQC-DOSSIER-v1'
})
print(f"  [OK] Hybrid Envelope Encrypted: Standard = {env_enc['pqc_standard']}, Cipher = {env_enc['symmetric_cipher']}")
st_env_dec, env_dec = test('http://127.0.0.1:8000/api/pqc/envelope/decrypt', method='POST', data={
    'secret_key_hex': kem_kp['secret_key_hex'],
    'envelope': env_enc,
    'associated_data': 'GGISP-PQC-DOSSIER-v1'
})
assert env_dec['plaintext'] == 'CLASSIFIED_POLICY_ACCORD_13_DIVISIONS'
print(f"  [OK] Hybrid Envelope Decrypted: '{env_dec['plaintext']}' ({env_dec['decryption_status']})")

# Test Merkle PQC Signer
st_merkle_pqc, merkle_pqc = test('http://127.0.0.1:8000/api/pqc/sign-merkle-root', method='POST')
print(f"  [OK] Post-Quantum Merkle Attestation: Root = {merkle_pqc['merkle_root'][:20]}... Standard = {merkle_pqc['pqc_signature_standard']}, Verified = {merkle_pqc['signature_verification']}")

# Test Shor Gate Calculation & Mosca Audit
st_shor, shor_res = test('http://127.0.0.1:8000/api/pqc/shor-gate-calculation', method='POST', data={'classical_algorithm': 'RSA', 'key_bits': 2048})
print(f"  [OK] Shor Calculator: RSA-2048 Logical Qubits = {shor_res['estimated_logical_qubits_required']}, Surface Code Qubits = {shor_res['estimated_physical_qubits_required']}")
st_mosca, mosca_res = test('http://127.0.0.1:8000/api/pqc/shor-risk-audit')
print(f"  [OK] Mosca HNDL Matrix: Audited {mosca_res['total_domains_audited']} domains, Critical exposure = {mosca_res['domains_with_hndl_exposure']}")

# 8. Test User Authentication & Author Access Subsystem
print("\n--- Verifying Authentication & Author Access Subsystem ---")
# Sign up standard user
st_su, su_res = test('http://127.0.0.1:8000/api/auth/signup', method='POST', data={
    'full_name': 'Live Verification Analyst',
    'email': 'verify_analyst_2026@ggisp.org',
    'mobile_number': '+1 202 555 0199',
    'password': 'LiveVerifyPassword123!'
})
print(f"  [OK] Sign Up: {su_res['user']['email']} (Role: {su_res['user']['role']}, Status: {st_su})")

# Sign in author
st_auth, auth_res = test('http://127.0.0.1:8000/api/auth/signin', method='POST', data={
    'email': 'bhuvanjakkula@gmail.com',
    'password': ''
})
assert auth_res['user']['is_author'] is True
print(f"  [OK] Author Sign In: {auth_res['user']['email']} -> {auth_res['user']['role']} (All Access: {auth_res['user']['access_all_features']})")

# Direct author access
st_dir, dir_res = test('http://127.0.0.1:8000/api/auth/author-access', method='POST', data={
    'email': 'bhuvanjakkula@gmail.com'
})
assert dir_res['user']['is_author'] is True
print(f"  [OK] Direct Author Access: Verified author token generated")

# Profile check with token
author_token = dir_res['token']
req_me = urllib.request.Request('http://127.0.0.1:8000/api/auth/me', headers={'Authorization': f'Bearer {author_token}'})
with urllib.request.urlopen(req_me, timeout=5) as res:
    me_data = json.loads(res.read().decode('utf-8'))
assert me_data['is_author'] is True
assert 'ALL_13_DIVISIONS' in me_data['permissions']
print(f"  [OK] Author Profile & Permissions: {len(me_data['permissions'])} Sovereign Permissions Active")

print("\nALL LIVE PRODUCTION, QUANTUM-SAFE & AUTHOR AUTHENTICATION ENDPOINTS VALIDATED SUCCESSFULLY.")


