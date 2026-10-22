'use strict';
const $ = id => document.getElementById(id);
const state = {engines: [], domains: [], projects: [], engine: null, parameters: {}, project: null, snapshots: [], datasets: [], snapshot: null, tab: 'studio'};
const nice = s => s.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
const number = v => typeof v === 'number' ? new Intl.NumberFormat(undefined, {maximumFractionDigits: 4}).format(v) : v === null ? 'Not defined' : String(v);
function el(tag, text, cls) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (cls) e.className = cls; return e; }
function option(select, value, text) { const o = el('option', text); o.value = value; select.append(o); }
function announce(text, error = false) { const n = $('notice'); n.textContent = text; n.className = 'notice' + (error ? ' error' : ''); n.hidden = false; if (error) n.scrollIntoView({behavior: 'smooth', block: 'nearest'}); }
async function api(url, body) {
  const response = await fetch(url, body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : (data.detail || []).map(d => `${(d.loc || []).join(' → ')}: ${d.msg}`).join('\n') || 'Request failed');
  return data;
}
async function guard(fn, button) {
  if (button) button.disabled = true;
  try { return await fn(); } catch (error) { announce(error.message, true); }
  finally { if (button) button.disabled = false; }
}
function tab(name) {
  state.tab = name;
  document.querySelectorAll('.tab').forEach(e => e.hidden = e.id !== name);
  document.querySelectorAll('[data-tab]').forEach(e => e.classList.toggle('active', e.dataset.tab === name));
  if (name === 'studies') guard(loadStudies);
  if (name === 'assistant') guard(searchEvidence);
}
document.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => tab(b.dataset.tab));
document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => $(b.dataset.close).close());
$('new-project').onclick = () => $('project-dialog').showModal();

function resolve(schema) { return schema.$ref ? state.engine.input_schema.$defs[schema.$ref.split('/').pop()] : schema; }
function seed(raw) {
  const schema = resolve(raw);
  if (schema.default !== undefined) return structuredClone(schema.default);
  if (schema.type === 'object') return Object.fromEntries(Object.entries(schema.properties).map(([k,v]) => [k, k === 'division' ? state.project.domain_slug : seed(v)]));
  if (schema.type === 'array') return [];
  if (schema.type === 'boolean') return false;
  if (schema.type === 'string') return '';
  return schema.minimum !== undefined ? schema.minimum : schema.exclusiveMinimum !== undefined ? schema.exclusiveMinimum + 1 : 0;
}
function getPath(path) { return path.reduce((v,k) => v[k], state.parameters); }
function putPath(path, value) { const parent = path.slice(0,-1).reduce((v,k) => v[k], state.parameters); parent[path.at(-1)] = value; }

function renderFields(raw, value, path = []) {
  const schema = resolve(raw), grid = el('div', undefined, 'parameter-grid');
  Object.entries(schema.properties).forEach(([key, property]) => {
    const spec = resolve(property), fieldPath = [...path,key], id = 'param-' + fieldPath.join('-');
    const group = el('div', undefined, 'field-group');
    if (spec.type === 'array' && resolve(spec.items).type === 'object') {
      group.classList.add('array-group');
      const heading = el('div', undefined, 'array-heading'); heading.append(el('h4', nice(key)));
      const add = el('button', '+ Add record', 'secondary mini'); add.type = 'button';
      add.disabled = value[key].length >= (spec.maxItems || 100);
      add.onclick = () => { value[key].push(seed(spec.items)); renderParameters(); };
      heading.append(add); group.append(heading);
      value[key].forEach((row, index) => {
        const card = el('div', undefined, 'array-row'), top = el('div', undefined, 'row-heading');
        top.append(el('span', 'RECORD ' + String(index+1).padStart(2,'0')));
        const remove = el('button', 'Remove', 'text-button mini'); remove.type = 'button';
        remove.disabled = value[key].length <= (spec.minItems || 0);
        remove.onclick = () => { value[key].splice(index,1); renderParameters(); };
        top.append(remove); card.append(top, renderFields(spec.items, row, [...fieldPath,index])); group.append(card);
      });
      if (!value[key].length) group.append(el('p', 'No records. Add one if relevant to the study.', 'muted small'));
    } else {
      const label = el('label', nice(key)); label.htmlFor = id;
      let input;
      if (spec.type === 'boolean') {
        input = el('input'); input.type = 'checkbox'; input.checked = value[key]; label.className = 'check';
        input.onchange = () => putPath(fieldPath, input.checked); label.prepend(input); group.append(label);
      } else {
        if (key === 'division' || key.endsWith('_domain')) {
          input = el('select'); state.domains.forEach(d => option(input,d.slug,d.name)); input.value = value[key];
          input.onchange = () => putPath(fieldPath,input.value);
        } else {
          input = el('input');
          if (spec.type === 'number' || spec.type === 'integer') {
            input.type = 'number'; input.step = spec.type === 'integer' ? '1' : 'any'; input.required = true;
            if (spec.minimum !== undefined) input.min = spec.minimum;
            if (spec.maximum !== undefined) input.max = spec.maximum;
            input.value = value[key]; input.oninput = () => putPath(fieldPath, input.value === '' ? null : Number(input.value));
          } else if (spec.type === 'array') {
            input.type = 'text'; input.value = value[key].join(', '); input.required = spec.minItems > 0;
            const numeric = ['number','integer'].includes(resolve(spec.items).type);
            input.placeholder = numeric ? 'Numbers in scenario order, separated by commas' : 'Names separated by commas';
            input.oninput = () => putPath(fieldPath,input.value.split(',').map(s => s.trim()).filter(Boolean).map(s => numeric ? Number(s) : s));
          } else {
            input.type = 'text'; input.value = value[key]; input.required = spec.minLength > 0;
            if (spec.maxLength) input.maxLength = spec.maxLength;
            input.oninput = () => putPath(fieldPath,input.value);
          }
        }
        input.id = id; input.name = fieldPath.join('.'); group.append(label,input);
      }
      input.id = id;
    }
    grid.append(group);
  });
  return grid;
}
function renderParameters() { $('parameter-form').replaceChildren(renderFields(state.engine.input_schema,state.parameters)); }
function chooseEngine(id, parameters) {
  state.engine = state.engines.find(e => e.id === id);
  state.parameters = structuredClone(parameters || state.engine.example);
  $('engine-domain').textContent = state.domains.find(d => d.slug === state.engine.domain)?.name.toUpperCase() || state.engine.domain;
  $('engine-title').textContent = state.engine.title; $('engine-method').textContent = state.engine.method;
  $('method-references').replaceChildren();(state.engine.references || []).forEach(ref=>{const a=el('a',ref.title+' ↗');a.href=ref.url;a.target='_blank';a.rel='noopener noreferrer';$('method-references').append(a,el('br'));});
  $('study-name').value = state.engine.title + ' / working study';
  $('result-panel').hidden = true; $('sensitivity-results').replaceChildren();
  $('assumptions-note').value = ''; renderParameters(); renderEngineList();
  $('sensitivity-field').replaceChildren();
  Object.entries(state.engine.input_schema.properties).filter(([,s]) => ['integer','number'].includes(s.type)).forEach(([k]) => option($('sensitivity-field'), k, nice(k)));
  const available = $('sensitivity-field').options.length > 0;
  $('sensitivity-form').hidden = !available; $('sensitivity-empty').hidden = available;
  if (available) setSensitivityDefaults();
}
function renderEngineList() {
  const query = $('engine-search').value.toLowerCase(); $('engine-list').replaceChildren();
  const tier = $('engine-tier').value;
  state.engines.forEach((engine,index) => {
    const domain = state.domains.find(d => d.slug === engine.domain)?.name || engine.domain;
    if (!(engine.title + domain).toLowerCase().includes(query)) return;
    if (tier === 'advanced' && engine.tier !== 'advanced') return;
    if (tier === 'foundation' && engine.tier === 'advanced') return;
    if (tier === 'project' && !(engine.applicable_domains || [engine.domain]).includes(state.project.domain_slug)) return;
    const b = el('button', undefined, 'engine-button' + (state.engine?.id === engine.id ? ' active' : '')); b.type = 'button';
    b.setAttribute('aria-pressed', String(state.engine?.id === engine.id));
    const text = el('span'); text.append(el('strong',engine.tier === 'advanced' ? engine.title : domain), el('small',engine.tier === 'advanced' ? 'ADVANCED · '+domain : engine.title));
    b.append(el('span',String(index+1).padStart(2,'0'),'number'),text); b.onclick = () => chooseEngine(engine.id); $('engine-list').append(b);
  });
}
$('engine-search').oninput = renderEngineList;
$('engine-tier').onchange = renderEngineList;
$('reset-inputs').onclick = () => chooseEngine(state.engine.id);

function table(rows) {
  const box = el('div');
  if (!rows.length) { box.append(el('p','No row-level results for this calculation.','muted small')); return box; }
  const keys = [...new Set(rows.flatMap(r => Object.keys(r)))], t = el('table'), head = el('thead'), hr = el('tr');
  keys.forEach(k => hr.append(el('th',nice(k)))); head.append(hr); t.append(head);
  const body = el('tbody'); rows.slice(0,2000).forEach(r => { const tr = el('tr'); keys.forEach(k => tr.append(el('td',number(r[k])))); body.append(tr); }); t.append(body); box.append(t); return box;
}
function chart(rows) {
  const box = $('result-chart'); box.replaceChildren();
  const axis = rows[0] && typeof rows[0].day === 'number' ? 'day' : 'year';
  if (rows.length < 2 || !rows.every(r => typeof r[axis] === 'number')) return;
  let keys = Object.keys(rows[0]).filter(k => k !== axis && typeof rows[0][k] === 'number');
  if (keys.includes('policy_infectious')) keys = ['baseline_infectious','policy_infectious'];
  keys = keys.slice(0,4); if (!keys.length) return;
  const vals = rows.flatMap(r => keys.map(k => r[k])), low = Math.min(...vals), high = Math.max(...vals), span = high-low || 1;
  const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns,'svg'); svg.setAttribute('viewBox','0 0 760 270'); svg.classList.add('chart'); svg.setAttribute('role','img'); svg.setAttribute('aria-label',keys.map(nice).join(', ')+' over '+axis+'s. Exact values appear in the table below.');
  const text = (x,y,s) => { const t = document.createElementNS(ns,'text'); t.setAttribute('x',x); t.setAttribute('y',y); t.setAttribute('font-size','11'); t.setAttribute('fill','#657987'); t.textContent = s; svg.append(t); };
  for (let i=0;i<4;i++) { const y=30+i*50, line=document.createElementNS(ns,'line'); line.setAttribute('x1','65');line.setAttribute('x2','735');line.setAttribute('y1',y);line.setAttribute('y2',y);line.setAttribute('stroke','#e1eae5');svg.append(line);text(0,y+4,number(high-i*(high-low)/3)); }
  const palette=['#087c67','#4168bc','#b47724','#9c5a90'];
  keys.forEach((key,index)=>{const line=document.createElementNS(ns,'polyline');line.setAttribute('fill','none');line.setAttribute('stroke',palette[index]);line.setAttribute('stroke-width','2.5');line.setAttribute('points',rows.map((r,i)=>`${65+i/(rows.length-1)*670},${180-(r[key]-low)/span*150}`).join(' '));svg.append(line);text(65+(index%2)*345,240+Math.floor(index/2)*17,'● '+nice(key));svg.lastChild.setAttribute('fill',palette[index]);});text(65,210,nice(axis)+' '+rows[0][axis]);text(675,210,nice(axis)+' '+rows.at(-1)[axis]);box.append(svg);
}
function showResults(out, savedId) {
  $('result-panel').hidden = false; $('metrics').replaceChildren();
  $('result-context').textContent = `${state.engines.find(e => e.id === out.engine_id)?.title || out.engine_id} · method version ${out.model_version} · user-supplied assumptions`;
  Object.entries(out.metrics).forEach(([k,v]) => { const m=el('div',undefined,'metric');m.append(el('strong',number(v)),el('small',nice(k)));$('metrics').append(m); });
  $('result-table').replaceChildren(table(out.rows)); chart(out.rows); $('result-limits').textContent = out.limitations; $('result-links').replaceChildren();
  if (savedId) { const a=el('a','Download results CSV ↗','button secondary');a.href=`/api/analyses/${savedId}/results.csv`;const b=el('button','Recalculate & verify','secondary');b.type='button';b.onclick=()=>guard(async()=>{const r=await api(`/api/analyses/${savedId}/reproduce`,{});announce(r.matches?'Recalculated output matches the saved model output.':'Recalculated output differs from the saved study.',!r.matches);},b);$('result-links').append(a,b); }
}
function analysisPayload() { return {name:$('study-name').value,parameters:state.parameters,assumptions_note:$('assumptions-note').value,snapshot_ids:[...$('snapshot-refs').selectedOptions].map(o=>Number(o.value)),dataset_ids:[...$('dataset-refs').selectedOptions].map(o=>Number(o.value))}; }
$('analysis-form').onsubmit=e=>{e.preventDefault();guard(async()=>showResults(await api(`/api/engines/${state.engine.id}/calculate`,analysisPayload())),e.submitter);};
$('save-analysis').onclick=()=>{if(!$('analysis-form').reportValidity())return;guard(async()=>{const r=await api(`/api/projects/${$('project').value}/analyses/${state.engine.id}`,analysisPayload());showResults(r,r.id);announce(`Study ${r.id} saved with model version and evidence references. SHA-256: ${r.sha256}`);},$('save-analysis'));};
function setSensitivityDefaults(){const key=$('sensitivity-field').value,spec=state.engine.input_schema.properties[key],base=state.parameters[key];let values=[base*0.9,base,base*1.1];if(base===0)values=[0,1,2];values=values.map(v=>spec.type==='integer'?Math.round(v):Number(v.toPrecision(6)));if(spec.minimum!==undefined)values=values.map(v=>Math.max(v,spec.minimum));if(spec.maximum!==undefined)values=values.map(v=>Math.min(v,spec.maximum));$('sensitivity-values').value=[...new Set(values)].join(', ');}
$('sensitivity-field').onchange=setSensitivityDefaults;
$('sensitivity-form').onsubmit=e=>{e.preventDefault();guard(async()=>{const parts=$('sensitivity-values').value.split(',').map(s=>s.trim());if(parts.some(p=>!p||!Number.isFinite(Number(p))))throw Error('Enter finite numbers separated by commas.');const r=await api(`/api/engines/${state.engine.id}/sensitivity`,{parameters:state.parameters,field:$('sensitivity-field').value,values:parts.map(Number)});$('sensitivity-results').replaceChildren(table(r.rows));},e.submitter);};

async function loadProject(){
  const pid=$('project').value;if(!pid)return;
  const [project,snapshots,datasets,spans]=await Promise.all([api(`/api/projects/${pid}`),api(`/api/projects/${pid}/snapshots`),api(`/api/projects/${pid}/datasets`),api(`/api/projects/${pid}/evidence-spans`)]);
  state.project=project;state.snapshots=snapshots;state.datasets=datasets;$('brief').href=`/api/projects/${pid}/brief.md`;
  renderEngineList();
  $('study-detail').hidden=true;$('result-panel').hidden=true;
  [$('snapshot-source'),$('dataset-source')].forEach(select=>{select.replaceChildren();option(select,'','Select a registered source…');project.sources.forEach(s=>option(select,s.id,s.title));});
  $('source-list').replaceChildren();
  project.sources.forEach(s=>{const record=el('div',undefined,'record');record.append(el('h4',`S${s.id} · ${s.title}`),el('p',`${s.publisher} · ${s.manually_reviewed?'Personal review attested':'Awaiting personal review'}`,'muted'));const link=el('a','Open source ↗');link.href=s.url;link.target='_blank';link.rel='noopener noreferrer';record.append(link);
    const details=el('details'),summary=el('summary','Record personal review findings'),form=el('form'),note=el('textarea'),label=el('label','What you examined, what it supports, and its limits'),check=el('input'),cl=el('label','I personally examined this source.','check'),save=el('button','Save review attestation','secondary');note.id=`source-review-note-${s.id}`;label.htmlFor=note.id;note.required=true;note.minLength=20;note.maxLength=3000;check.type='checkbox';check.required=true;cl.prepend(check);save.type='submit';form.append(label,note,cl,save);form.onsubmit=e=>{e.preventDefault();guard(async()=>{await api(`/api/projects/${pid}/sources/${s.id}/review`,{note:note.value,confirmed_human_review:check.checked});await loadProject();announce('Personal source review recorded. This is not independent verification.');},save);};details.append(summary,form);record.append(details);$('source-list').append(record);});
  $('snapshot-refs').replaceChildren();snapshots.forEach(s=>option($('snapshot-refs'),s.id,`S${s.source_id} · ${s.title}`));
  $('dataset-refs').replaceChildren();datasets.forEach(d=>option($('dataset-refs'),d.id,d.name));
  $('snapshot-count').textContent=snapshots.length;$('snapshot-list').replaceChildren();
  snapshots.forEach(s=>{const r=el('div',undefined,'record');r.append(el('h4',s.title),el('p',`Source S${s.source_id} · ${s.characters} characters · ${s.created_at}`,'muted'),el('p',s.sha256,'hash'));const b=el('button','Read & link a passage','secondary mini');b.onclick=()=>guard(()=>openSnapshot(s.id),b);r.append(b);$('snapshot-list').append(r);});
  $('dataset-list').replaceChildren();datasets.forEach(d=>{const r=el('div',undefined,'record');r.append(el('h4',d.name),el('p',`Source S${d.source_id} · ${d.created_at}`,'muted'),el('p',d.sha256,'hash'));const b=el('button','Inspect observations','secondary mini');b.onclick=()=>guard(async()=>{const data=await api(`/api/projects/${pid}/datasets/${d.id}`);$('dataset-dialog-title').textContent=d.name;$('dataset-view').replaceChildren(table(data.rows));$('dataset-dialog').showModal();},b);r.append(b);$('dataset-list').append(r);});
  $('span-list').replaceChildren();if(!spans.length)$('span-list').append(el('p','No exact passage links recorded yet.','empty'));
  spans.forEach(s=>{const r=el('div',undefined,'record');r.append(el('h4',`Claim C${s.claim_id} → snapshot ${s.snapshot_id}`),el('p',s.quote,'quote'),el('p',s.note,'muted'));$('span-list').append(r);});
  if(state.tab==='studies')await loadStudies();if(state.tab==='assistant')await searchEvidence();
}
$('project').onchange=()=>guard(loadProject);
$('project-form').onsubmit=e=>{e.preventDefault();guard(async()=>{const r=await api('/api/projects',{title:$('project-title').value,problem:$('project-problem').value,domain_slug:$('project-domain').value});state.projects=await api('/api/projects');renderProjects(r.id);await loadProject();const engine=state.engines.find(e=>e.domain===state.project.domain_slug);chooseEngine(engine.id);$('project-dialog').close();announce('Research project created. Define the evidence and assumptions before interpreting model outputs.');e.target.reset();},e.submitter);};
function renderProjects(selected){$('project').replaceChildren();state.projects.forEach(p=>option($('project'),p.id,p.title));if(selected)$('project').value=selected;}
$('source-form').onsubmit=e=>{e.preventDefault();guard(async()=>{await api(`/api/projects/${$('project').value}/sources`,{title:$('source-title').value,url:$('source-url').value,publisher:$('source-publisher').value,manually_reviewed:$('source-reviewed').checked});e.target.reset();await loadProject();announce('Source registered. You can now preserve text or import observations.');},e.submitter);};
$('snapshot-form').onsubmit=e=>{e.preventDefault();guard(async()=>{const r=await api(`/api/projects/${$('project').value}/snapshots`,{source_id:Number($('snapshot-source').value),title:$('snapshot-title').value,content:$('snapshot-content').value});e.target.reset();await loadProject();announce(`Snapshot ${r.id} saved. ${r.label}`);},e.submitter);};
$('dataset-form').onsubmit=e=>{e.preventDefault();guard(async()=>{const r=await api(`/api/projects/${$('project').value}/datasets`,{source_id:Number($('dataset-source').value),name:$('dataset-name').value,csv_text:$('dataset-csv').value});e.target.reset();await loadProject();announce(`Dataset ${r.id}: ${r.observations} observations imported. ${r.label}`);},e.submitter);};
$('world-bank-form').onsubmit=e=>{e.preventDefault();guard(async()=>{const r=await api(`/api/projects/${$('project').value}/imports/world-bank`,{country:$('wb-country').value,indicator:$('wb-indicator').value,start_year:Number($('wb-start').value),end_year:Number($('wb-end').value)});await loadProject();announce(`Imported ${r.observations} World Bank observations; ${r.missing_observations_skipped} missing values skipped. ${r.label}`);},e.submitter);};
async function openSnapshot(id){state.snapshot=await api(`/api/projects/${$('project').value}/snapshots/${id}`);$('snapshot-dialog-title').textContent=state.snapshot.title;$('snapshot-view').textContent=state.snapshot.content;$('span-claim').replaceChildren();state.project.claims.filter(c=>c.source_id===state.snapshot.source_id).forEach(c=>option($('span-claim'),c.id,`C${c.id} · ${c.statement}`));if(!$('span-claim').options.length)option($('span-claim'),'','Create a claim linked to this source in Research & personal advice');$('span-quote').value='';$('span-note').value='';$('snapshot-dialog').showModal();}
$('span-form').onsubmit=e=>{e.preventDefault();guard(async()=>{const quote=$('span-quote').value,content=state.snapshot.content,start=content.indexOf(quote);if(start<0)throw Error('The quotation must exactly match text in this snapshot.');const offset=Array.from(content.slice(0,start)).length;await api(`/api/projects/${$('project').value}/evidence-spans`,{claim_id:Number($('span-claim').value),snapshot_id:state.snapshot.id,start_offset:offset,end_offset:offset+Array.from(quote).length,quote,note:$('span-note').value});$('snapshot-dialog').close();await loadProject();announce('Exact source passage linked to the claim. Its evidence status has not changed.');},e.submitter);};

async function searchEvidence(){const r=await api(`/api/projects/${$('project').value}/research-assistant?q=${encodeURIComponent($('evidence-query').value)}`);$('search-hits').replaceChildren();if(!r.hits.length)$('search-hits').append(el('p','No matching preserved passages. Add snapshots or try different words.','empty'));r.hits.forEach(hit=>{const card=el('div',undefined,'record');card.append(el('h4',hit.title),el('p',`Snapshot ${hit.snapshot_id} · source S${hit.source_id} · matched terms: ${hit.matched_terms.join(', ')}`,'muted'),el('p',hit.excerpt,'quote'));const b=el('button','Inspect source passage','secondary mini');b.onclick=()=>guard(()=>openSnapshot(hit.snapshot_id),b);card.append(b);$('search-hits').append(card);});$('research-tasks').replaceChildren();r.research_tasks.forEach(t=>$('research-tasks').append(el('li',t)));$('suggested-engines').replaceChildren();r.suggested_engines.forEach(id=>{const b=el('button','Open '+state.engines.find(e=>e.id===id).title,'secondary');b.onclick=()=>{chooseEngine(id);tab('studio');};$('suggested-engines').append(b);});}
$('search-form').onsubmit=e=>{e.preventDefault();guard(searchEvidence,e.submitter);};
async function loadStudies(){const rows=await api(`/api/projects/${$('project').value}/analyses`);$('study-list').replaceChildren();rows.forEach(r=>{const card=el('div',undefined,'record');card.append(el('h4',r.name),el('p',`${state.engines.find(e=>e.id===r.engine_id)?.title || r.engine_id} · ${r.created_at}`,'muted'),el('p',r.sha256,'hash'));const b=el('button','Open study & review','secondary mini');b.onclick=()=>guard(()=>openStudy(r.id),b);card.append(b);$('study-list').append(card);});}
async function openStudy(id){
  const run=await api(`/api/analyses/${id}`),p=run.payload,box=$('study-detail');box.hidden=false;box.replaceChildren();box.append(el('h2',run.name),el('p',`Content integrity: ${run.integrity_ok?'matches saved hash':'MISMATCH'} · Evidence integrity: ${run.reference_integrity_ok?'matches':'MISMATCH'} · model ${p.outputs.model_version}`,'muted'),el('p',p.outputs.method,'method'));
  const actions=el('div',undefined,'actions'),load=el('button','Load assumptions into studio'),verify=el('button','Recalculate & verify','secondary'),csv=el('a','Export CSV ↗','button secondary');csv.href=`/api/analyses/${id}/results.csv`;
  load.disabled=!run.integrity_ok;verify.disabled=!run.integrity_ok||!run.reference_integrity_ok;
  load.onclick=()=>{chooseEngine(p.engine_id,p.inputs);$('study-name').value=p.name;$('assumptions-note').value=p.assumptions_note;for(const o of $('snapshot-refs').options)o.selected=p.references.source_snapshots.some(r=>r.id===Number(o.value));for(const o of $('dataset-refs').options)o.selected=p.references.datasets.some(r=>r.id===Number(o.value));tab('studio');showResults(p.outputs,id);};
  verify.onclick=()=>guard(async()=>{const r=await api(`/api/analyses/${id}/reproduce`,{});announce(r.matches?'Recomputed result matches the saved output.':'Recomputed result differs.',!r.matches);},verify);
  actions.append(load,verify,csv);box.append(actions,el('h3','Inputs & evidence references'));const pre=el('pre',JSON.stringify({inputs:p.inputs,references:p.references,assumptions:p.assumptions_note},null,2),'json-view');box.append(pre,el('p',p.mapping_note,'muted small'),table(p.outputs.rows),el('p',p.outputs.limitations,'limit'),el('h3','Human review history'));
  if(!run.reviews.length)box.append(el('p','No review recorded.','muted'));
  run.reviews.forEach(r=>{const record=el('div',undefined,'record');record.append(el('h4',`${r.reviewer} · ${nice(r.verdict)}`),el('p',r.note),el('p',r.created_at,'muted'));box.append(record);});
  const form=el('form');form.append(el('h3','Record a human review'));
  const reviewer=el('input');reviewer.id='reviewer';reviewer.required=true;reviewer.minLength=2;reviewer.maxLength=120;const rl=el('label','Reviewer name');rl.htmlFor=reviewer.id;
  const verdict=el('select');verdict.id='review-verdict';option(verdict,'needs_changes','Needs changes');option(verdict,'reviewed_with_limits','Reviewed with stated limitations');const vl=el('label','Review outcome');vl.htmlFor=verdict.id;
  const note=el('textarea');note.id='review-note';note.required=true;note.minLength=20;note.maxLength=4000;const nl=el('label','Findings, limitations and required changes');nl.htmlFor=note.id;
  const checked=el('input');checked.type='checkbox';checked.required=true;const cl=el('label','I personally reviewed the assumptions, sources and outputs.','check');cl.prepend(checked);
  const save=el('button','Save review');save.type='submit';form.append(rl,reviewer,vl,verdict,nl,note,cl,save,el('p','Review records are self-attested. This local application does not authenticate reviewer identity or independence.','muted small'));
  form.onsubmit=e=>{e.preventDefault();guard(async()=>{await api(`/api/analyses/${id}/reviews`,{reviewer:reviewer.value,verdict:verdict.value,note:note.value,confirmed_human_review:checked.checked});await openStudy(id);announce('Human review recorded in the audit trail.');},save);};box.append(form);box.scrollIntoView({behavior:'smooth',block:'start'});
}

guard(async()=>{const [engines,domains,projects,connectors]=await Promise.all([api('/api/engines'),api('/api/domains'),api('/api/projects'),api('/api/connectors')]);state.engines=engines;state.domains=domains;state.projects=projects;$('engine-count').textContent=engines.length;connectors.world_bank.indicators.forEach(i=>option($('wb-indicator'),i.id,i.name));state.domains.forEach(d=>option($('project-domain'),d.slug,d.name));renderProjects();await loadProject();const engine=state.engines.find(e=>e.domain===state.project.domain_slug)||state.engines[0];chooseEngine(engine.id);});
