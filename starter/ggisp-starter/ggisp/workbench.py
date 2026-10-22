"""Multi-domain analysis, evidence snapshots, reproducibility and review APIs."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ggisp.db import db
from ggisp.engines import ENGINES, calculate_engine

router=APIRouter()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def init_workbench(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS source_snapshots (
        id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id),
        source_id INTEGER NOT NULL REFERENCES sources(id), title TEXT NOT NULL,
        content TEXT NOT NULL, sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS evidence_spans (
        id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id),
        claim_id INTEGER NOT NULL REFERENCES claims(id), snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
        start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL, quote TEXT NOT NULL,
        note TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id),
        source_id INTEGER NOT NULL REFERENCES sources(id), name TEXT NOT NULL,
        rows_json TEXT NOT NULL, sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS analysis_runs (
        id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id),
        engine_id TEXT NOT NULL, name TEXT NOT NULL, payload_json TEXT NOT NULL,
        sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS analysis_reviews (
        id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES analysis_runs(id),
        reviewer TEXT NOT NULL, verdict TEXT NOT NULL, note TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS source_reviews (
        id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id),
        source_id INTEGER NOT NULL REFERENCES sources(id), note TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS analysis_project ON analysis_runs(project_id);
    CREATE INDEX IF NOT EXISTS snapshot_project ON source_snapshots(project_id);
    CREATE INDEX IF NOT EXISTS evidence_claim ON evidence_spans(claim_id);
    """)


def require_project(con,pid):
    row=con.execute('SELECT * FROM projects WHERE id=?',(pid,)).fetchone()
    if row is None: raise HTTPException(404,'Project not found')
    return dict(row)


def audit(con,pid,action,kind,rid):
    con.execute('INSERT INTO audit_log(project_id,action,record_type,record_id) VALUES (?,?,?,?)',(pid,action,kind,rid))


def engine_info(engine_id):
    if engine_id not in ENGINES: raise HTTPException(404,'Unknown analytical engine')
    return ENGINES[engine_id]


def evaluate(engine_id,parameters):
    engine_info(engine_id)
    try:
        return calculate_engine(engine_id,parameters)
    except ValidationError as exc:
        # Exclude Pydantic's raw exception context, which is not JSON serializable.
        raise HTTPException(422,jsonable_encoder(exc.errors(include_context=False,include_input=False))) from exc
    except (ValueError,OverflowError) as exc:
        raise HTTPException(422,'The supplied assumptions exceed the model numerical range') from exc


class Request(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)


class Analysis(Request):
    name: str=Field(min_length=3,max_length=150)
    parameters: dict[str,Any]
    snapshot_ids: list[int]=Field(default_factory=list,max_length=100)
    dataset_ids: list[int]=Field(default_factory=list,max_length=30)
    assumptions_note: str=Field(default='',max_length=4000)

    @field_validator('snapshot_ids','dataset_ids')
    @classmethod
    def no_duplicates(cls,value):
        if len(value)!=len(set(value)) or any(i<=0 for i in value):
            raise ValueError('References must be unique positive record identifiers')
        return value


class Snapshot(Request):
    source_id: int=Field(gt=0)
    title: str=Field(min_length=3,max_length=180)
    content: str=Field(min_length=10,max_length=200000)


class Span(Request):
    claim_id: int=Field(gt=0)
    snapshot_id: int=Field(gt=0)
    start_offset: int=Field(ge=0)
    end_offset: int=Field(gt=0)
    quote: str=Field(min_length=1,max_length=10000)
    note: str=Field(min_length=3,max_length=2000)


class DatasetImport(Request):
    source_id: int=Field(gt=0)
    name: str=Field(min_length=3,max_length=150)
    csv_text: str=Field(min_length=20,max_length=500000)


class Sensitivity(Request):
    parameters: dict[str,Any]
    field: str=Field(min_length=1,max_length=100)
    values: list[float]=Field(min_length=2,max_length=15)


class Review(Request):
    reviewer: str=Field(min_length=2,max_length=120)
    verdict: str=Field(pattern='^(needs_changes|reviewed_with_limits)$')
    note: str=Field(min_length=20,max_length=4000)
    confirmed_human_review: bool


class SourceReview(Request):
    note: str=Field(min_length=20,max_length=3000)
    confirmed_human_review: bool


@router.get('/workbench',include_in_schema=False)
def page():
    return FileResponse(Path(__file__).with_name('workbench.html'))


@router.get('/methods',include_in_schema=False)
def method_document():
    return PlainTextResponse(Path(__file__).resolve().parent.parent.joinpath('docs/ADVANCED-METHODS-v0.5.md').read_text(encoding='utf-8'))


@router.get('/assets/{name}',include_in_schema=False)
def asset(name: str):
    if name not in ('workbench.js','workbench.css'):
        raise HTTPException(404,'Asset not found')
    return FileResponse(Path(__file__).with_name(name))


@router.get('/api/engines')
def catalog():
    return [{"id":key,**{k:v for k,v in e.items() if k not in ('schema','calculate')},
             "input_schema":e['schema'].model_json_schema(),"status":"Illustrative research tool"}
            for key,e in ENGINES.items()]


@router.post('/api/engines/{engine_id}/calculate')
def calculate(engine_id: str,data: Analysis):
    inputs,output=evaluate(engine_id,data.parameters)
    return {'inputs':inputs,**output}


@router.post('/api/engines/{engine_id}/sensitivity')
def sensitivity(engine_id: str,data: Sensitivity):
    engine=engine_info(engine_id)
    schema=engine['schema'].model_json_schema()['properties']
    if data.field not in schema or schema[data.field].get('type') not in ('integer','number'):
        raise HTTPException(422,'Choose a top-level numeric input field from this engine')
    rows=[]
    for value in data.values:
        _,out=evaluate(engine_id,{**data.parameters,data.field:value})
        rows.append({'input_value':value,**out['metrics']})
    return {'engine_id':engine_id,'field':data.field,'rows':rows,
            'method':'One-at-a-time deterministic sensitivity; all other inputs are fixed.',
            'limitations':'Not a probability interval, causal estimate or joint uncertainty model.'}


@router.post('/api/projects/{pid}/analyses/{engine_id}',status_code=201)
def save_analysis(pid: int,engine_id: str,data: Analysis):
    inputs,output=evaluate(engine_id,data.parameters)
    with db() as con:
        require_project(con,pid)
        references={}
        for table,ids in (('source_snapshots',data.snapshot_ids),('datasets',data.dataset_ids)):
            references[table]=[]
            for rid in ids:
                record=con.execute(f'SELECT * FROM {table} WHERE id=? AND project_id=?',(rid,pid)).fetchone()
                if record is None: raise HTTPException(400,'Evidence references must belong to this project')
                actual=hashlib.sha256(record['content'].encode('utf-8')).hexdigest() if table=='source_snapshots' else fingerprint(json.loads(record['rows_json']))
                if actual!=record['sha256']: raise HTTPException(409,'Referenced evidence content does not match its stored hash')
                references[table].append({'id':rid,'sha256':record['sha256']})
        payload={'engine_id':engine_id,'name':data.name,'inputs':inputs,'outputs':output,
                 'references':references,'assumptions_note':data.assumptions_note,
                 'mapping_note':'References record provenance. Parameter values are entered by the researcher; datasets are not automatically mapped to model inputs.'}
        digest=fingerprint(payload)
        cur=con.execute('INSERT INTO analysis_runs(project_id,engine_id,name,payload_json,sha256) VALUES (?,?,?,?,?)',
                        (pid,engine_id,data.name,canonical(payload),digest))
        rid=cur.lastrowid
        audit(con,pid,'save_analysis','analysis_run',rid)
    return {'id':rid,'sha256':digest,**output}


@router.get('/api/projects/{pid}/analyses')
def analyses(pid: int):
    with db() as con:
        require_project(con,pid)
        return [dict(r) for r in con.execute('SELECT id,engine_id,name,sha256,created_at FROM analysis_runs WHERE project_id=? ORDER BY id DESC',(pid,))]


@router.get('/api/analyses/{rid}')
def detail(rid: int):
    with db() as con:
        r=con.execute('SELECT * FROM analysis_runs WHERE id=?',(rid,)).fetchone()
        if r is None: raise HTTPException(404,'Analysis not found')
        result=dict(r)
        result['reviews']=[dict(r) for r in con.execute('SELECT * FROM analysis_reviews WHERE run_id=? ORDER BY id DESC',(rid,))]
    result['payload']=json.loads(result.pop('payload_json'))
    result['integrity_ok']=fingerprint(result['payload'])==result['sha256']
    reference_issues=[]
    with db() as con:
        for table,references in result['payload']['references'].items():
            # Fixed table names only, even if a local database has been edited.
            if table not in ('source_snapshots','datasets'):
                reference_issues.append('Unknown reference table'); continue
            for ref in references:
                record=con.execute(f'SELECT * FROM {table} WHERE id=? AND project_id=?',(ref['id'],result['project_id'])).fetchone()
                if record is None:
                    reference_issues.append(f"Missing {table} record {ref['id']}"); continue
                actual=hashlib.sha256(record['content'].encode('utf-8')).hexdigest() if table=='source_snapshots' else fingerprint(json.loads(record['rows_json']))
                if actual!=ref['sha256']:
                    reference_issues.append(f"Changed {table} record {ref['id']}")
    result['reference_integrity_ok']=not reference_issues
    result['reference_integrity_issues']=reference_issues
    return result


@router.post('/api/analyses/{rid}/reproduce')
def reproduce(rid: int):
    run=detail(rid)
    if not run['integrity_ok']: raise HTTPException(409,'Stored content hash does not match')
    if not run['reference_integrity_ok']: raise HTTPException(409,'Referenced evidence has changed or is missing')
    payload=run['payload']
    engine=engine_info(payload['engine_id'])
    if payload['outputs']['model_version']!=engine['version']:
        raise HTTPException(409,'The stored engine version differs from the installed version')
    _,output=evaluate(payload['engine_id'],payload['inputs'])
    return {'id':rid,'matches':canonical(output)==canonical(payload['outputs']),
            'label':'Recalculation agreement only; not independent model validation'}


def safe_cell(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):
        return "'"+value
    return value


@router.get('/api/analyses/{rid}/results.csv')
def export_csv(rid: int):
    run=detail(rid)
    if not run['integrity_ok']: raise HTTPException(409,'Stored content hash does not match')
    out=run['payload']['outputs']; stream=io.StringIO(newline=''); writer=csv.writer(stream)
    writer.writerow(['engine_id','model_version','sha256','section','row','field','value'])
    for key,val in out['metrics'].items():
        writer.writerow([out['engine_id'],out['model_version'],run['sha256'],'metrics',0,key,safe_cell(val)])
    for i,row in enumerate(out['rows']):
        for key,val in row.items():
            writer.writerow([out['engine_id'],out['model_version'],run['sha256'],'results',i,key,safe_cell(val)])
    return PlainTextResponse(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="ggisp-analysis-{rid}.csv"'})


@router.post('/api/analyses/{rid}/reviews',status_code=201)
def review(rid: int,data: Review):
    if not data.confirmed_human_review: raise HTTPException(400,'Confirm human review')
    run=detail(rid)
    if not run['integrity_ok']: raise HTTPException(409,'Stored content hash does not match')
    with db() as con:
        cur=con.execute('INSERT INTO analysis_reviews(run_id,reviewer,verdict,note) VALUES (?,?,?,?)',(rid,data.reviewer,data.verdict,data.note))
        audit(con,run['project_id'],'record_review','analysis_review',cur.lastrowid)
    return {'id':cur.lastrowid,'label':'Local human attestation; reviewer identity and independence are not authenticated'}


@router.post('/api/projects/{pid}/snapshots',status_code=201)
def snapshot(pid: int,data: Snapshot):
    digest=hashlib.sha256(data.content.encode('utf-8')).hexdigest()
    with db() as con:
        require_project(con,pid)
        if not con.execute('SELECT 1 FROM sources WHERE id=? AND project_id=?',(data.source_id,pid)).fetchone():
            raise HTTPException(400,'Source must belong to this project')
        cur=con.execute('INSERT INTO source_snapshots(project_id,source_id,title,content,sha256) VALUES (?,?,?,?,?)',
                        (pid,data.source_id,data.title,data.content,digest))
        audit(con,pid,'save_snapshot','source_snapshot',cur.lastrowid)
    return {'id':cur.lastrowid,'sha256':digest,'label':'Researcher-pasted source text; origin and truth are not verified by its hash'}


@router.post('/api/projects/{pid}/sources/{sid}/review',status_code=201)
def review_source(pid: int,sid: int,data: SourceReview):
    if not data.confirmed_human_review: raise HTTPException(400,'Confirm that you personally examined this source')
    with db() as con:
        require_project(con,pid)
        if not con.execute('SELECT 1 FROM sources WHERE id=? AND project_id=?',(sid,pid)).fetchone():
            raise HTTPException(404,'Source not found in this project')
        cur=con.execute('INSERT INTO source_reviews(project_id,source_id,note) VALUES (?,?,?)',(pid,sid,data.note))
        con.execute('UPDATE sources SET manually_reviewed=1 WHERE id=?',(sid,))
        audit(con,pid,'attest_source_review','source_review',cur.lastrowid)
    return {'id':cur.lastrowid,'label':'Personal review attestation, not independent source verification'}


@router.get('/api/projects/{pid}/source-reviews')
def source_reviews(pid: int):
    with db() as con:
        require_project(con,pid)
        return [dict(r) for r in con.execute('SELECT * FROM source_reviews WHERE project_id=? ORDER BY id DESC',(pid,))]


@router.get('/api/projects/{pid}/snapshots')
def snapshots(pid: int):
    with db() as con:
        require_project(con,pid)
        return [dict(r) for r in con.execute('SELECT id,source_id,title,sha256,created_at,length(content) AS characters FROM source_snapshots WHERE project_id=? ORDER BY id DESC',(pid,))]


@router.get('/api/projects/{pid}/snapshots/{sid}')
def snapshot_detail(pid: int,sid: int):
    with db() as con:
        require_project(con,pid)
        r=con.execute('SELECT * FROM source_snapshots WHERE id=? AND project_id=?',(sid,pid)).fetchone()
        if r is None: raise HTTPException(404,'Snapshot not found')
        result=dict(r)
        result['integrity_ok']=hashlib.sha256(result['content'].encode('utf-8')).hexdigest()==result['sha256']
        return result


@router.post('/api/projects/{pid}/evidence-spans',status_code=201)
def citation(pid: int,data: Span):
    with db() as con:
        require_project(con,pid)
        claim=con.execute('SELECT * FROM claims WHERE id=? AND project_id=?',(data.claim_id,pid)).fetchone()
        snap=con.execute('SELECT * FROM source_snapshots WHERE id=? AND project_id=?',(data.snapshot_id,pid)).fetchone()
        if claim is None or snap is None: raise HTTPException(400,'Claim and snapshot must belong to this project')
        if hashlib.sha256(snap['content'].encode('utf-8')).hexdigest()!=snap['sha256']:
            raise HTTPException(409,'Snapshot content does not match its stored hash')
        if claim['source_id']!=snap['source_id']: raise HTTPException(400,'Snapshot source must match the claim linked source')
        if data.end_offset>len(snap['content']) or data.start_offset>=data.end_offset or snap['content'][data.start_offset:data.end_offset]!=data.quote:
            raise HTTPException(422,'Quote must exactly match the specified Unicode code-point offsets')
        cur=con.execute('INSERT INTO evidence_spans(project_id,claim_id,snapshot_id,start_offset,end_offset,quote,note) VALUES (?,?,?,?,?,?,?)',
                        (pid,data.claim_id,data.snapshot_id,data.start_offset,data.end_offset,data.quote,data.note))
        audit(con,pid,'link_citation','evidence_span',cur.lastrowid)
    return {'id':cur.lastrowid,'label':'Exact text match, not an assessment of evidentiary support'}


@router.get('/api/projects/{pid}/evidence-spans')
def spans(pid: int):
    with db() as con:
        require_project(con,pid)
        return [dict(r) for r in con.execute('SELECT * FROM evidence_spans WHERE project_id=? ORDER BY id',(pid,))]


def parse_csv(text):
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')),strict=True)
    if reader.fieldnames!=['series','year','value','unit']:
        raise HTTPException(422,'CSV header must be exactly: series,year,value,unit')
    rows=[]; keys=set()
    try:
        for i,r in enumerate(reader):
            if i>=2000: raise ValueError('At most 2000 observations are accepted per dataset')
            if None in r or any(v is None for v in r.values()): raise ValueError('Every row must have exactly four cells')
            series=r['series'].strip(); unit=r['unit'].strip(); year=int(r['year']); value=float(r['value'])
            if not series or len(series)>120 or not unit or len(unit)>80 or not 1800<=year<=2200 or not math.isfinite(value) or abs(value)>1e15:
                raise ValueError('Invalid series, year, unit or finite value')
            key=(series,year)
            if key in keys: raise ValueError('Duplicate series and year observation')
            if any(x['series']==series and x['unit']!=unit for x in rows): raise ValueError('Each series must use one unit')
            keys.add(key); rows.append({'series':series,'year':year,'value':value,'unit':unit})
    except (ValueError,csv.Error) as exc:
        raise HTTPException(422,str(exc)) from exc
    if not rows: raise HTTPException(422,'Dataset must contain observations')
    return rows


@router.post('/api/projects/{pid}/datasets',status_code=201)
def import_dataset(pid: int,data: DatasetImport):
    rows=parse_csv(data.csv_text); digest=fingerprint(rows)
    with db() as con:
        require_project(con,pid)
        if not con.execute('SELECT 1 FROM sources WHERE id=? AND project_id=?',(data.source_id,pid)).fetchone():
            raise HTTPException(400,'Source must belong to this project')
        cur=con.execute('INSERT INTO datasets(project_id,source_id,name,rows_json,sha256) VALUES (?,?,?,?,?)',
                        (pid,data.source_id,data.name,canonical(rows),digest))
        audit(con,pid,'import_dataset','dataset',cur.lastrowid)
    return {'id':cur.lastrowid,'observations':len(rows),'sha256':digest,'label':'Syntax checked; source authority and values are not verified'}


@router.get('/api/projects/{pid}/datasets')
def datasets(pid: int):
    with db() as con:
        require_project(con,pid)
        return [dict(r) for r in con.execute('SELECT id,source_id,name,sha256,created_at FROM datasets WHERE project_id=? ORDER BY id DESC',(pid,))]


@router.get('/api/projects/{pid}/datasets/{did}')
def dataset_detail(pid: int,did: int):
    with db() as con:
        require_project(con,pid)
        row=con.execute('SELECT * FROM datasets WHERE project_id=? AND id=?',(pid,did)).fetchone()
        if row is None: raise HTTPException(404,'Dataset not found')
        result=dict(row)
    result['rows']=json.loads(result.pop('rows_json'))
    result['integrity_ok']=fingerprint(result['rows'])==result['sha256']
    return result


@router.get('/api/projects/{pid}/research-assistant')
def research_assistant(pid: int,q: str=Query(default='',max_length=300)):
    with db() as con:
        p=require_project(con,pid)
        claims=[dict(r) for r in con.execute('SELECT * FROM claims WHERE project_id=?',(pid,))]
        snap=[dict(r) for r in con.execute('SELECT id,source_id,title,content,sha256 FROM source_snapshots WHERE project_id=?',(pid,))]
        cited={r[0] for r in con.execute('SELECT DISTINCT claim_id FROM evidence_spans WHERE project_id=?',(pid,))}
    stopwords={'the','and','for','with','that','this','from','have','how','what','might','are','were','into','their','which','before','after','your'}
    tokens=set(re.findall(r'\w{3,}',(q or p['problem']).casefold()))-stopwords
    hits=[]
    for s in snap:
        text=s['content']; lower=text.casefold()
        matching=[t for t in sorted(tokens) if t in set(re.findall(r'\w{3,}',lower))]
        if not matching: continue
        # Return an exact stored-text excerpt; no generated factual assertions.
        start=max(0,lower.find(matching[0])-100); end=min(len(text),start+500)
        hits.append({'snapshot_id':s['id'],'source_id':s['source_id'],'title':s['title'],
                     'matched_terms':matching,'score':len(matching)/max(1,len(tokens)),
                     'excerpt':text[start:end],'sha256':s['sha256']})
    hits.sort(key=lambda x:(-x['score'],x['snapshot_id']))
    tasks=[f"Claim C{c['id']}: {'review disputed/unverified status' if c['evidence_status']!='supported' else 'attach exact source passage'}"
           for c in claims if c['evidence_status']!='supported' or c['id'] not in cited]
    if not snap: tasks.append('Paste and preserve reviewed primary-source passages')
    if not claims: tasks.append('Record source-linked claims and their uncertainties')
    tasks.append('Test alternative assumptions and obtain independent subject review')
    return {'mode':'Local lexical evidence retrieval; no generative AI and no external transmission',
            'question':p['problem'],'hits':hits[:10],'research_tasks':tasks,
            'suggested_engines':[key for key,e in ENGINES.items() if p['domain_slug'] in e.get('applicable_domains',[e['domain']])],
            'limitations':'Word overlap is not semantic verification. Quoted text is researcher-supplied and may be false or incomplete.'}


def brief_sections(pid):
    lines=['', '## Multi-domain analytical studies', '']
    for summary in analyses(pid):
        run=detail(summary['id']); payload=run['payload']; out=payload['outputs']
        lines.extend([f"### Analysis {run['id']}: {run['name']}",
                      f"Engine: {run['engine_id']} | Version: {out['model_version']} | Hash integrity: {run['integrity_ok']} | Evidence integrity: {run['reference_integrity_ok']}",
                      f"SHA-256: {run['sha256']}",f"Method: {out['method']}",
                      'Inputs: '+canonical(payload['inputs']),'Metrics: '+canonical(out['metrics']),
                      'Provenance: '+canonical(payload['references']),
                      'Assumptions note: '+payload['assumptions_note'],payload['mapping_note'],
                      'Limitations: '+out['limitations']])
        for review in run['reviews']:
            lines.append(f"Human review (self-attested): {review['reviewer']} / {review['verdict']} / {review['note']}")
    lines.extend(['','## Exact evidence passages',''])
    for span in spans(pid):
        snap=snapshot_detail(pid,span['snapshot_id'])
        lines.extend([f"Claim C{span['claim_id']} → snapshot {span['snapshot_id']} / source S{snap['source_id']}",
                      f"Text offsets: {span['start_offset']}:{span['end_offset']} | snapshot SHA-256: {snap['sha256']}",
                      'Quoted text (researcher supplied): '+span['quote'],'Researcher interpretation: '+span['note']])
    lines.extend(['','## Source review attestations',''])
    for review in source_reviews(pid):
        lines.append(f"Source S{review['source_id']} / {review['created_at']} / personal review: {review['note']}")
    return lines
