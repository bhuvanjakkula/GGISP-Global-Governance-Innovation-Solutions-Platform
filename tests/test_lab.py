from tests.conftest import make_project

def assumptions():
    return dict(initial_debt_percent_gdp=100,interest_rate_percent=5,nominal_gdp_growth_percent=5,primary_surplus_percent_gdp=0,years=5)

def payload():
    return dict(name='Reproducibility test',baseline=assumptions(),policy={**assumptions(),'primary_surplus_percent_gdp':1},stress={**assumptions(),'interest_rate_percent':8})

def test_compare_known_results(client):
    r=client.post('/api/lab/compare',json=payload())
    assert r.status_code==200
    summary=r.json()['summary']
    assert summary[0]['terminal_debt_percent_gdp']==100
    assert summary[1]['terminal_debt_percent_gdp']==95
    assert summary[2]['terminal_debt_percent_gdp']>100
    assert summary[0]['initial_stabilizing_surplus_percent_gdp']==0

def test_mismatched_horizon_rejected(client):
    p=payload();p['policy']['years']=3
    assert client.post('/api/lab/compare',json=p).status_code==422

def test_snapshot_persistence_hash_and_csv(client):
    pid=make_project(client)
    a=client.post(f'/api/projects/{pid}/runs',json=payload())
    assert a.status_code==201
    b=client.post(f'/api/projects/{pid}/runs',json=payload()).json()
    assert a.json()['sha256']==b['sha256']
    rid=a.json()['id']
    assert client.get(f'/api/runs/{rid}').json()['inputs']==payload()
    csv=client.get(f'/api/runs/{rid}/results.csv')
    assert len(csv.text.splitlines())==19
    assert a.json()['sha256'] in csv.text
    assert len(client.get(f'/api/projects/{pid}/runs').json())==2
    assert any(x['action']=='save_model_run' for x in client.get(f'/api/projects/{pid}').json()['audit_log'])

def test_missing_entities(client):
    assert client.post('/api/projects/99999/runs',json=payload()).status_code==404
    assert client.get('/api/projects/99999/runs').status_code==404
    assert client.get('/api/runs/99999').status_code==404
    assert client.get('/api/projects/99999/readiness').status_code==404

def test_readiness_and_pages(client):
    pid=make_project(client)
    r=client.get(f'/api/projects/{pid}/readiness').json()
    assert r['saved_runs']==0 and r['supported_claims']==0
    assert len(r['next_actions'])==5
    assert client.get('/lab').status_code==200
    assert '/lab' in client.get('/').text

