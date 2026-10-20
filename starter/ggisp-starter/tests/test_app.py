import pytest
from fastapi.testclient import TestClient

from ggisp.main import app
from ggisp.modelling import DebtAssumptions, simulate


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GGISP_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(app) as client:
        yield client


def make_project(client):
    response = client.post('/api/projects', json={
        'domain_slug': 'sovereign-debt', 'title': 'Debt and development test',
        'problem': 'What happens to illustrative debt paths with different interest rate assumptions?'
    })
    assert response.status_code == 201, response.text
    return response.json()['id']


def test_thirteen_domains_and_demo(client):
    assert len(client.get('/api/domains').json()) == 13
    assert len(client.get('/api/projects').json()) >= 1


def test_create_source_claim_recommendation_export(client):
    pid = make_project(client)
    source = client.post(f'/api/projects/{pid}/sources', json={
        'title': 'Official illustrative data documentation',
        'url': 'https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api',
        'publisher': 'World Bank', 'notes': 'A documentation source, not proof of country outcomes.',
        'manually_reviewed': True,
    })
    assert source.status_code == 201, source.text
    sid = source.json()['id']
    claim = client.post(f'/api/projects/{pid}/claims', json={
        'statement': 'The linked documentation describes a public indicators API.',
        'evidence_status': 'supported', 'source_id': sid,
        'limitations': 'Does not prove debt outcomes for any country.'
    })
    assert claim.status_code == 201, claim.text
    rec = client.post(f'/api/projects/{pid}/recommendations', json={
        'recommendation': 'Conduct an independent scenario comparison before negotiating restructuring.',
        'rationale': 'Transparent assumptions allow independent review of options.',
        'risks': 'Simplified scenarios omit distributional effects and political constraints.',
        'author': 'Founder'
    })
    assert rec.status_code == 201
    rid = rec.json()['id']
    assert client.post(f'/api/recommendations/{rid}/approve',json={'confirmed_human_review':True}).status_code == 200
    brief = client.get(f'/api/projects/{pid}/brief.md')
    assert brief.status_code == 200
    assert 'INTERNAL RESEARCH DRAFT' in brief.text
    assert 'Conduct an independent scenario comparison' in brief.text
    assert 'Founder examined source: yes' in brief.text


def test_cannot_approve_without_source_support(client):
    pid = make_project(client)
    response = client.post(f'/api/projects/{pid}/recommendations', json={
        'recommendation': 'Request expert review of new preliminary policy ideas.',
        'rationale': 'Independent scrutiny can discover hidden limitations.',
        'risks': 'Unvalidated claims may mislead decision-makers.',
        'author': 'Founder'
    })
    rid = response.json()['id']
    assert client.post(f'/api/recommendations/{rid}/approve',json={'confirmed_human_review':True}).status_code == 400


def test_supported_claim_requires_reviewed_linked_source(client):
    pid = make_project(client)
    response = client.post(f'/api/projects/{pid}/claims',json={
        'statement': 'This is a tentative claim about policy evidence.', 'evidence_status':'supported'
    })
    assert response.status_code == 400


def test_source_url_rejects_non_http(client):
    pid = make_project(client)
    response = client.post(f'/api/projects/{pid}/sources',json={
        'title':'Bad protocol', 'publisher':'Unknown', 'url':'file:///etc/passwd'
    })
    assert response.status_code == 422


def test_debt_identity(client):
    r = client.post('/api/debt/simulate',json={
        'initial_debt_percent_gdp':100,'interest_rate_percent':5,
        'nominal_gdp_growth_percent':5,'primary_surplus_percent_gdp':0,'years':3
    })
    assert r.status_code == 200
    assert all(row['debt_percent_gdp']==100 for row in r.json()['values'])


def test_bad_debt_growth_rejected(client):
    r = client.post('/api/debt/simulate',json={
        'initial_debt_percent_gdp':100,'interest_rate_percent':5,
        'nominal_gdp_growth_percent':-100,'primary_surplus_percent_gdp':0,'years':3
    })
    assert r.status_code == 422


def test_ai_is_opt_in_and_unconfigured(client):
    pid = make_project(client)
    response = client.post(f'/api/projects/{pid}/ai-draft',json={'confirmed_external_ai_transfer':False})
    assert response.status_code == 400
    response = client.post(f'/api/projects/{pid}/ai-draft',json={'confirmed_external_ai_transfer':True})
    assert response.status_code == 503
