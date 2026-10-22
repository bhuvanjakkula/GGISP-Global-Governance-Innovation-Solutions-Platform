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
