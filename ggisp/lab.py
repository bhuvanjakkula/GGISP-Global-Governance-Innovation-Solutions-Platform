"""Reproducible, local decision support. No external data or AI required."""
import csv
import hashlib
import io
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field, model_validator
from ggisp.db import db
from ggisp.modelling import DebtAssumptions, simulate

router = APIRouter()
VERSION = 'debt-comparison-1.0'

class Comparison(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    baseline: DebtAssumptions
    policy: DebtAssumptions
    stress: DebtAssumptions

    @model_validator(mode='after')
    def comparable(self):
        for a in (self.policy, self.stress):
            if a.years != self.baseline.years or a.initial_debt_percent_gdp != self.baseline.initial_debt_percent_gdp:
                raise ValueError('Scenarios must share starting debt and horizon')
        return self

def calculate(data):
    results = {k: simulate(getattr(data, k)) for k in ('baseline','policy','stress')}
    base = results['baseline']['values'][-1]['debt_percent_gdp']
    summary = []
    for name, result in results.items():
        a = result['assumptions']
        end = result['values'][-1]['debt_percent_gdp']
        # Initial-year surplus needed to hold initial debt/GDP constant.
        stabilizer = a['initial_debt_percent_gdp'] * ((1+a['interest_rate_percent']/100)/(1+a['nominal_gdp_growth_percent']/100)-1)
        summary.append({'scenario':name,'terminal_debt_percent_gdp':end,
                        'difference_from_baseline_pp':round(end-base,3),
                        'initial_stabilizing_surplus_percent_gdp':round(stabilizer,3)})
    return {'model_version':VERSION,'scenarios':results,'summary':summary,
            'limitations':'Illustrative constant-assumption arithmetic, not a forecast. Negative debt represents net assets in this simplified equation. No country data or uncertainty probabilities are supplied.'}

@router.get('/lab', include_in_schema=False)
def lab():
    return FileResponse(Path(__file__).with_name('lab.html'))

@router.post('/api/lab/compare')
def compare(data: Comparison):
    return calculate(data)

@router.post('/api/projects/{project_id}/runs', status_code=201)
def save(project_id: int, data: Comparison):
    output = calculate(data)
    inputs = json.dumps(data.model_dump(),sort_keys=True,separators=(',',':'))
    outputs = json.dumps(output,sort_keys=True,separators=(',',':'))
    digest = hashlib.sha256((VERSION+'\n'+inputs+'\n'+outputs).encode()).hexdigest()
    with db() as con:
        if not con.execute('SELECT 1 FROM projects WHERE id=?',(project_id,)).fetchone():
            raise HTTPException(404,'Project not found')
        cur=con.execute('INSERT INTO scenario_runs(project_id,name,input_json,output_json,sha256,model_version) VALUES (?,?,?,?,?,?)',
                        (project_id,data.name,inputs,outputs,digest,VERSION))
        rid=cur.lastrowid
        con.execute('INSERT INTO audit_log(project_id,action,record_type,record_id) VALUES (?,?,?,?)',
                    (project_id,'save_model_run','scenario_run',rid))
    return {'id':rid,'sha256':digest,**output}

@router.get('/api/projects/{project_id}/runs')
def runs(project_id: int):
    with db() as con:
        if not con.execute('SELECT 1 FROM projects WHERE id=?',(project_id,)).fetchone():
            raise HTTPException(404,'Project not found')
        return [dict(r) for r in con.execute('SELECT id,name,sha256,model_version,created_at FROM scenario_runs WHERE project_id=? ORDER BY id DESC',(project_id,))]

@router.get('/api/runs/{run_id}')
def run_detail(run_id: int):
    with db() as con:
        r=con.execute('SELECT * FROM scenario_runs WHERE id=?',(run_id,)).fetchone()
        if r is None: raise HTTPException(404,'Run not found')
        result=dict(r)
    result['inputs']=json.loads(result.pop('input_json'))
    result['outputs']=json.loads(result.pop('output_json'))
    return result

@router.get('/api/runs/{run_id}/results.csv')
def download_csv(run_id: int):
    r=run_detail(run_id)
    stream=io.StringIO(newline=''); writer=csv.writer(stream)
    writer.writerow(['model_version','sha256','scenario','year','debt_percent_gdp'])
    for name, scenario in r['outputs']['scenarios'].items():
        for value in scenario['values']:
            writer.writerow([r['model_version'],r['sha256'],name,value['year'],value['debt_percent_gdp']])
    return PlainTextResponse(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="ggisp-run-{run_id}.csv"'})

@router.get('/api/projects/{project_id}/readiness')
def readiness(project_id: int):
    with db() as con:
        if not con.execute('SELECT 1 FROM projects WHERE id=?',(project_id,)).fetchone():
            raise HTTPException(404,'Project not found')
        reviewed=con.execute('SELECT COUNT(*) FROM sources WHERE project_id=? AND manually_reviewed=1',(project_id,)).fetchone()[0]
        unsupported=con.execute("SELECT COUNT(*) FROM claims WHERE project_id=? AND evidence_status!='supported'",(project_id,)).fetchone()[0]
        supported=con.execute("SELECT COUNT(*) FROM claims WHERE project_id=? AND evidence_status='supported'",(project_id,)).fetchone()[0]
        model_runs=con.execute('SELECT COUNT(*) FROM scenario_runs WHERE project_id=?',(project_id,)).fetchone()[0]
        model_runs+=con.execute('SELECT COUNT(*) FROM analysis_runs WHERE project_id=?',(project_id,)).fetchone()[0]
        recs=con.execute('SELECT COUNT(*) FROM recommendations WHERE project_id=?',(project_id,)).fetchone()[0]
    tasks=[]
    if not reviewed: tasks.append('Examine and record primary sources')
    if not supported: tasks.append('Link a supported claim to reviewed evidence')
    if unsupported: tasks.append(f'Resolve or disclose {unsupported} unverified/disputed claims')
    if not model_runs: tasks.append('Save a baseline, policy and stress comparison')
    if not recs: tasks.append('Write your recommendation, mechanism and risks')
    tasks.append('Obtain independent domain review before external use')
    return {'reviewed_sources':reviewed,'supported_claims':supported,'unresolved_claims':unsupported,'saved_runs':model_runs,'recommendations':recs,'next_actions':tasks,'label':'Workflow completeness only; not scientific validation'}
