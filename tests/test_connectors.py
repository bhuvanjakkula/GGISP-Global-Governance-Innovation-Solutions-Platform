import json

import pytest
from fastapi import HTTPException

from tests.conftest import make_project
from ggisp import connectors


REQUEST={'country':'IND','indicator':'SP.POP.TOTL','start_year':2020,'end_year':2022}


def response():
    return [{'pages':1,'lastupdated':'2026-01-01'},[
        {'indicator':{'id':'SP.POP.TOTL'},'countryiso3code':'IND','date':'2020','value':100},
        {'indicator':{'id':'SP.POP.TOTL'},'countryiso3code':'IND','date':'2021','value':None},
        {'indicator':{'id':'SP.POP.TOTL'},'countryiso3code':'IND','date':'2022','value':110}]]


def test_world_bank_import_preserves_response_and_metadata(client,monkeypatch):
    urls=[]
    def fetch(url):
        urls.append(url)
        return json.dumps(response())
    monkeypatch.setattr(connectors,'fetch_text',fetch)
    pid=make_project(client)
    r=client.post(f'/api/projects/{pid}/imports/world-bank',json=REQUEST)
    assert r.status_code==201,r.text
    data=r.json()
    assert data['observations']==2 and data['missing_observations_skipped']==1
    assert urls[0].startswith('https://api.worldbank.org/v2/country/IND/indicator/SP.POP.TOTL?')
    assert client.get(f"/api/projects/{pid}/datasets/{data['dataset_id']}").json()['rows'][1]['year']==2022
    assert client.get(f"/api/projects/{pid}/snapshots/{data['snapshot_id']}").json()['content']==json.dumps(response())
    assert client.get(f'/api/projects/{pid}').json()['sources'][0]['manually_reviewed']==0


def test_invalid_import_inputs_and_missing_project_do_not_request_network(client,monkeypatch):
    def forbidden(url):raise AssertionError('Network must not be called')
    monkeypatch.setattr(connectors,'fetch_text',forbidden)
    pid=make_project(client)
    for changes in [{'country':'../'}, {'indicator':'evil'}, {'start_year':2023,'end_year':2020}, {'start_year':1960,'end_year':2025}]:
        assert client.post(f'/api/projects/{pid}/imports/world-bank',json={**REQUEST,**changes}).status_code==422
    assert client.post('/api/projects/99999/imports/world-bank',json=REQUEST).status_code==404


@pytest.mark.parametrize('bad',['not json',json.dumps([{'pages':2},[]]),json.dumps([{},[]])])
def test_bad_or_empty_upstream_data_does_not_write_partial_records(client,monkeypatch,bad):
    monkeypatch.setattr(connectors,'fetch_text',lambda _:bad)
    pid=make_project(client)
    r=client.post(f'/api/projects/{pid}/imports/world-bank',json=REQUEST)
    assert r.status_code in (404,502)
    assert client.get(f'/api/projects/{pid}').json()['sources']==[]
    assert client.get(f'/api/projects/{pid}/datasets').json()==[]


def test_mismatched_series_and_network_error(client,monkeypatch):
    bad=response();bad[1][0]['countryiso3code']='USA'
    monkeypatch.setattr(connectors,'fetch_text',lambda _:json.dumps(bad))
    pid=make_project(client)
    assert client.post(f'/api/projects/{pid}/imports/world-bank',json=REQUEST).status_code==502
    def failure(_):raise HTTPException(502,'Provider unavailable')
    monkeypatch.setattr(connectors,'fetch_text',failure)
    assert client.post(f'/api/projects/{pid}/imports/world-bank',json=REQUEST).status_code==502


def test_untrusted_host_rejected(client):
    assert client.get('/api/engines',headers={'Host':'evil.example'}).status_code==400

