"""Explicit, bounded imports from the fixed official World Bank API endpoint."""
from __future__ import annotations

import hashlib
import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ggisp.db import db
from ggisp.workbench import audit, canonical, fingerprint, require_project

router=APIRouter()
INDICATORS={
    'SP.POP.TOTL':('Population, total','people'),
    'NY.GDP.MKTP.CD':('GDP, current US dollars','current USD'),
    'NY.GDP.MKTP.KD.ZG':('GDP growth, annual percent','annual percent'),
    'GC.DOD.TOTL.GD.ZS':('Central government debt, percent of GDP','percent of GDP'),
    'SH.XPD.CHEX.GD.ZS':('Current health expenditure, percent of GDP','percent of GDP'),
}


class WorldBankImport(BaseModel):
    model_config=ConfigDict(extra='forbid')
    country: str=Field(pattern='^[A-Z]{3}$')
    indicator: str=Field(min_length=3,max_length=40)
    start_year: int=Field(ge=1960,le=2100)
    end_year: int=Field(ge=1960,le=2100)

    @model_validator(mode='after')
    def check(self):
        if self.indicator not in INDICATORS: raise ValueError('Choose an indicator from the connector catalog')
        if self.end_year<self.start_year or self.end_year-self.start_year>60:
            raise ValueError('Use an ordered range of at most 61 years')
        return self


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def fetch_text(url):
    request=Request(url,headers={'Accept':'application/json','User-Agent':'GGISP-local-research/0.4'})
    try:
        with build_opener(NoRedirect()).open(request,timeout=15) as response:
            content=response.read(1000001)
            if len(content)>1000000: raise HTTPException(502,'Provider response exceeds the import size limit')
            return content.decode('utf-8-sig')
    except (HTTPError,URLError,TimeoutError,OSError,UnicodeError) as exc:
        raise HTTPException(502,'World Bank data could not be retrieved. Retry later or use CSV import.') from exc


def normalize(text,data):
    try:
        response=json.loads(text)
        if not isinstance(response,list) or len(response)!=2 or not isinstance(response[0],dict) or not isinstance(response[1],list):
            raise ValueError('Unexpected provider response shape')
        if int(response[0].get('pages',1))>1: raise ValueError('Provider returned an incomplete paginated result')
        if len(response[1])>2000: raise ValueError('Too many observations')
        rows=[]; missing=0; years=set()
        for record in response[1]:
            if record['indicator']['id']!=data.indicator or record.get('countryiso3code')!=data.country:
                raise ValueError('Provider country or indicator differs from the requested series')
            year=int(record['date'])
            if not data.start_year<=year<=data.end_year or year in years: raise ValueError('Unexpected or duplicate observation year')
            years.add(year)
            if record['value'] is None:
                missing+=1; continue
            if isinstance(record['value'],bool): raise ValueError('Observation cannot be a boolean')
            value=float(record['value'])
            if not math.isfinite(value) or abs(value)>1e15: raise ValueError('Invalid finite observation value')
            rows.append({'series':data.country+':'+data.indicator,'year':year,'value':value,'unit':INDICATORS[data.indicator][1]})
        if not rows: raise HTTPException(404,'No nonmissing observations for the selected country, indicator and years')
        return sorted(rows,key=lambda r:r['year']),missing,str(response[0].get('lastupdated','not supplied'))[:80]
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        raise HTTPException(502,'Provider returned inconsistent data; no records were imported') from exc


@router.get('/api/connectors')
def catalog():
    return {'world_bank':{'status':'On-demand public API import','indicators':[
        {'id':key,'name':value[0],'unit':value[1]} for key,value in INDICATORS.items()],
        'documentation':'https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries'},
        'imf':{'status':'Not connected; use attributed CSV imports'},
        'wto':{'status':'Not connected; use attributed CSV imports'}}


@router.post('/api/projects/{pid}/imports/world-bank',status_code=201)
def import_world_bank(pid: int,data: WorldBankImport):
    # Resolve project before any external request; never send local project content.
    with db() as con: require_project(con,pid)
    url=f'https://api.worldbank.org/v2/country/{data.country}/indicator/{data.indicator}?format=json&per_page=2000&date={data.start_year}:{data.end_year}'
    text=fetch_text(url)
    rows,missing,updated=normalize(text,data)
    title=f'World Bank {data.country} / {data.indicator} / {data.start_year}-{data.end_year}'
    with db() as con:
        require_project(con,pid)
        sid=con.execute('INSERT INTO sources(project_id,title,url,publisher,notes,manually_reviewed) VALUES (?,?,?,?,?,0)',
                        (pid,title,url,'World Bank',f'Imported via the public Indicators API. Provider lastupdated: {updated}. Missing observations skipped: {missing}. Not human reviewed.')).lastrowid
        snap=con.execute('INSERT INTO source_snapshots(project_id,source_id,title,content,sha256) VALUES (?,?,?,?,?)',
                         (pid,sid,title+' / API response',text,hashlib.sha256(text.encode('utf-8')).hexdigest())).lastrowid
        did=con.execute('INSERT INTO datasets(project_id,source_id,name,rows_json,sha256) VALUES (?,?,?,?,?)',
                        (pid,sid,title,canonical(rows),fingerprint(rows))).lastrowid
        for kind,rid in [('source',sid),('source_snapshot',snap),('dataset',did)]: audit(con,pid,'world_bank_import',kind,rid)
    return {'source_id':sid,'snapshot_id':snap,'dataset_id':did,'observations':len(rows),
            'missing_observations_skipped':missing,'provider_last_updated':updated,
            'label':'Retrieved from the official API. Human source review and model suitability checks remain required.'}
