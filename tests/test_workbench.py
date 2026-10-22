"""End-to-end project provenance, reproducibility, review and export checks."""
import json
import sqlite3
from copy import deepcopy

import pytest

from tests.conftest import make_project
from ggisp.engines import ENGINES


def source(client,pid):
    r=client.post(f'/api/projects/{pid}/sources',json={'title':'Synthetic source for tests',
        'url':'https://example.org/research','publisher':'Test publisher','manually_reviewed':True})
    assert r.status_code==201
    return r.json()['id']


def snapshot(client,pid,sid,text='Resources need transparent allocation and reviewed evidence.'):
    r=client.post(f'/api/projects/{pid}/snapshots',json={'source_id':sid,'title':'Preserved passage','content':text})
    assert r.status_code==201,r.text
    return r.json()['id']


def payload(engine='climate'):
    return {'name':'Test analytical study','parameters':deepcopy(ENGINES[engine]['example'])}


@pytest.mark.parametrize('engine',list(ENGINES))
def test_every_engine_http_endpoint(client,engine):
    r=client.post(f'/api/engines/{engine}/calculate',json=payload(engine))
    assert r.status_code==200,r.text
    assert r.json()['engine_id']==engine


def test_catalog_assets_and_unknown_routes(client):
    catalog=client.get('/api/engines').json()
    assert len(catalog)==20 and 'input_schema' in catalog[0]
    for path in ['/workbench','/assets/workbench.js','/assets/workbench.css']:
        assert client.get(path).status_code==200
    assert client.get('/assets/main.py').status_code==404
    assert client.post('/api/engines/unknown/calculate',json=payload()).status_code==404
    assert client.get('/api/analyses/999').status_code==404


def test_analysis_provenance_review_reproduce_and_brief(client):
    pid=make_project(client);sid=source(client,pid);snap=snapshot(client,pid,sid)
    p={**payload(),'snapshot_ids':[snap],'assumptions_note':'All values are synthetic; no causal estimate.'}
    a=client.post(f'/api/projects/{pid}/analyses/climate',json=p)
    assert a.status_code==201,a.text
    rid=a.json()['id']
    b=client.post(f'/api/projects/{pid}/analyses/climate',json=p)
    assert a.json()['sha256']==b.json()['sha256']
    detail=client.get(f'/api/analyses/{rid}').json()
    assert detail['integrity_ok']
    assert detail['payload']['references']['source_snapshots'][0]['id']==snap
    assert client.post(f'/api/analyses/{rid}/reproduce',json={}).json()['matches'] is True
    review={'reviewer':'Test reviewer','verdict':'needs_changes','note':'Check assumptions and independent source context.','confirmed_human_review':False}
    assert client.post(f'/api/analyses/{rid}/reviews',json=review).status_code==400
    review['confirmed_human_review']=True
    assert client.post(f'/api/analyses/{rid}/reviews',json=review).status_code==201
    assert len(client.get(f'/api/analyses/{rid}').json()['reviews'])==1
    exported=client.get(f'/api/analyses/{rid}/results.csv')
    assert exported.status_code==200 and a.json()['sha256'] in exported.text
    brief=client.get(f'/api/projects/{pid}/brief.md').text
    assert 'All values are synthetic' in brief and 'Test reviewer' in brief
    assert a.json()['sha256'] in brief
    actions={r['action'] for r in client.get(f'/api/projects/{pid}').json()['audit_log']}
    assert {'save_analysis','record_review','save_snapshot'}<=actions


def test_integrity_tampering_is_detected(client,monkeypatch):
    import os
    pid=make_project(client)
    rid=client.post(f'/api/projects/{pid}/analyses/climate',json=payload()).json()['id']
    with sqlite3.connect(os.environ['GGISP_DB_PATH']) as con:
        con.execute("UPDATE analysis_runs SET payload_json=replace(payload_json,'Test analytical study','Tampered name') WHERE id=?",(rid,))
    assert not client.get(f'/api/analyses/{rid}').json()['integrity_ok']
    assert client.post(f'/api/analyses/{rid}/reproduce',json={}).status_code==409
    assert client.get(f'/api/analyses/{rid}/results.csv').status_code==409


def test_cross_project_references_are_rejected(client):
    a=make_project(client);b=make_project(client);sid=source(client,a);snap=snapshot(client,a,sid)
    assert client.post(f'/api/projects/{b}/analyses/climate',json={**payload(),'snapshot_ids':[snap]}).status_code==400
    assert client.post(f'/api/projects/{b}/snapshots',json={'source_id':sid,'title':'Wrong project','content':'This source belongs elsewhere.'}).status_code==400
    assert client.get(f'/api/projects/{b}/snapshots/{snap}').status_code==404


def test_unicode_exact_passage_links_and_search(client):
    pid=make_project(client);sid=source(client,pid)
    text='🧭 Research: transparent allocation protects resources.'
    snap=snapshot(client,pid,sid,text)
    claim=client.post(f'/api/projects/{pid}/claims',json={'statement':'A claim about transparent allocation.','source_id':sid}).json()['id']
    quote='transparent allocation';start=text.index(quote)
    p={'claim_id':claim,'snapshot_id':snap,'start_offset':start,'end_offset':start+len(quote),'quote':quote,'note':'Synthetic quoted wording; not empirical proof.'}
    assert client.post(f'/api/projects/{pid}/evidence-spans',json={**p,'quote':'incorrect quotation'}).status_code==422
    assert client.post(f'/api/projects/{pid}/evidence-spans',json=p).status_code==201
    assert client.get(f'/api/projects/{pid}').json()['claims'][0]['evidence_status']=='unverified'
    r=client.get(f'/api/projects/{pid}/research-assistant?q=transparent%20allocation').json()
    assert r['hits'][0]['snapshot_id']==snap
    assert quote in r['hits'][0]['excerpt']
    assert 'transparent allocation' in client.get(f'/api/projects/{pid}/brief.md').text


def test_dataset_import_validates_rows_and_provenance(client):
    pid=make_project(client);sid=source(client,pid)
    p={'source_id':sid,'name':'Synthetic emissions','csv_text':'series,year,value,unit\nEmissions,2024,100,tonnes\nEmissions,2025,90,tonnes\n'}
    r=client.post(f'/api/projects/{pid}/datasets',json=p)
    assert r.status_code==201,r.text
    did=r.json()['id']
    assert r.json()['observations']==2
    assert client.get(f'/api/projects/{pid}/datasets/{did}').json()['integrity_ok']
    analysis=client.post(f'/api/projects/{pid}/analyses/climate',json={**payload(),'dataset_ids':[did]})
    assert analysis.status_code==201
    assert client.get(f'/api/projects/{pid}/datasets').json()[0]['id']==did
    for bad in ['series,year,value,unit\nA,2024,nan,x',
                'series,year,value,unit\nA,2024,1,x\nA,2024,2,x',
                'series,year,value,unit\nA,2024,1,x\nA,2025,2,y',
                'series,year,value,unit\nA,2024,1,x,extra',
                'series,year,value,unit\nA,1700,1,x',
                'bad,header\n1,2']:
        assert client.post(f'/api/projects/{pid}/datasets',json={**p,'csv_text':bad}).status_code==422


def test_sensitivity_varies_only_one_field(client):
    p=payload()['parameters']
    r=client.post('/api/engines/climate/sensitivity',json={'parameters':p,'field':'reduction_percent','values':[0,20,40]})
    assert r.status_code==200
    rows=r.json()['rows']
    assert rows[0]['cumulative_avoided_tonnes']==0
    assert rows[2]['cumulative_avoided_tonnes']==2*rows[1]['cumulative_avoided_tonnes']
    assert client.post('/api/engines/climate/sensitivity',json={'parameters':p,'field':'reduction_percent','values':[0,101]}).status_code==422
    assert client.post('/api/engines/portfolio/sensitivity',json={'parameters':payload('portfolio')['parameters'],'field':'investments','values':[1,2]}).status_code==422


def test_csv_export_neutralizes_formula_labels(client):
    pid=make_project(client);p=payload('trade');p['parameters']['items'][0]['name']='=1+1'
    rid=client.post(f'/api/projects/{pid}/analyses/trade',json=p).json()['id']
    text=client.get(f'/api/analyses/{rid}/results.csv').text
    assert "'=1+1" in text


@pytest.mark.parametrize('engine',list(ENGINES))
def test_all_engines_save_reproduce_and_export(client,engine):
    pid=make_project(client)
    r=client.post(f'/api/projects/{pid}/analyses/{engine}',json=payload(engine))
    assert r.status_code==201,r.text
    rid=r.json()['id']
    assert client.post(f'/api/analyses/{rid}/reproduce',json={}).json()['matches']
    assert client.get(f'/api/analyses/{rid}/results.csv').status_code==200


def test_referenced_evidence_tampering_blocks_reproduction(client):
    import os
    pid=make_project(client);sid=source(client,pid);snap=snapshot(client,pid,sid)
    p={**payload(),'snapshot_ids':[snap]}
    rid=client.post(f'/api/projects/{pid}/analyses/climate',json=p).json()['id']
    with sqlite3.connect(os.environ['GGISP_DB_PATH']) as con:
        con.execute("UPDATE source_snapshots SET content='Changed source passage that no longer matches' WHERE id=?",(snap,))
    run=client.get(f'/api/analyses/{rid}').json()
    assert run['integrity_ok'] and not run['reference_integrity_ok']
    assert client.post(f'/api/analyses/{rid}/reproduce',json={}).status_code==409
    assert client.post(f'/api/projects/{pid}/analyses/climate',json=p).status_code==409


def test_schema_initialization_is_idempotent_and_preserves_projects(client):
    from ggisp.db import init_db
    pid=make_project(client)
    sid=source(client,pid)
    init_db();init_db()
    assert client.get(f'/api/projects/{pid}').json()['sources'][0]['id']==sid
    assert len(client.get('/api/engines').json())==20


def test_imported_source_can_receive_a_confirmed_review(client):
    pid=make_project(client)
    sid=client.post(f'/api/projects/{pid}/sources',json={'title':'Unreviewed source','url':'https://example.org/source','publisher':'Example'}).json()['id']
    p={'note':'I checked the supplied context and documented its limitations.','confirmed_human_review':False}
    assert client.post(f'/api/projects/{pid}/sources/{sid}/review',json=p).status_code==400
    p['confirmed_human_review']=True
    assert client.post(f'/api/projects/{pid}/sources/{sid}/review',json=p).status_code==201
    assert client.get(f'/api/projects/{pid}').json()['sources'][0]['manually_reviewed']==1
    assert client.get(f'/api/projects/{pid}/source-reviews').json()[0]['note']==p['note']
    assert p['note'] in client.get(f'/api/projects/{pid}/brief.md').text
    other=make_project(client)
    assert client.post(f'/api/projects/{other}/sources/{sid}/review',json=p).status_code==404

