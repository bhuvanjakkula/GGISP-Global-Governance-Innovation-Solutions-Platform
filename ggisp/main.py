"""GGISP Platform v0.2: Global Governance, Innovation & Solutions Platform.
Unified research, evidence verification, official data hub, and human-approved policy advisory.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

from ggisp.ai.assistant import run_ai_draft
from ggisp.briefs.generator import generate_markdown_brief
from ggisp.db import calculate_hash, db, init_db
from ggisp.external_data.service import OfficialDataService
from ggisp.modelling.cross_domain import CrossDomainAssumptions, simulate_cross_domain
from ggisp.modelling.development_finance import (
    DevelopmentFinanceAssumptions,
    simulate_development_allocation,
)
from ggisp.modelling.sovereign_debt import (
    DynamicDebtAssumptions,
    simulate_debt,
)

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("GGISP Platform v0.2 initialized successfully.")
    yield


app = FastAPI(
    title="GGISP — Global Governance, Innovation & Solutions Platform",
    description="Unified international research, mathematical models, official data, and human-authored policy guidance.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_service = OfficialDataService()


def serialize(row):
    return dict(row) if row is not None else None


def ensure_project(con: sqlite3.Connection, project_id: int):
    row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


def audit(con: sqlite3.Connection, pid: int, action: str, record_type: str, rid: int, details: str = ""):
    con.execute(
        "INSERT INTO audit_log (project_id, action, record_type, record_id, details) VALUES (?, ?, ?, ?, ?)",
        (pid, action, record_type, rid, details),
    )


# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------

class ProjectCreate(BaseModel):
    domain_slug: str
    title: str = Field(min_length=4, max_length=180)
    problem: str = Field(min_length=15, max_length=4000)
    country_code: str = Field(default="KEN", min_length=2, max_length=10)


class SourceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    url: str = Field(min_length=10, max_length=1500)
    publisher: str = Field(min_length=2, max_length=150)
    publication_year: int | None = Field(default=None, ge=1900, le=2050)
    doi: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=4000)
    manually_reviewed: bool = False
    quality_rating: str = Field(default="unrated", pattern=r"^(high|medium|low|unrated)$")

    @field_validator("url")
    @classmethod
    def valid_url(cls, val: str) -> str:
        u = urlsplit(val)
        if u.scheme not in ("http", "https") or not u.netloc or u.username or u.password:
            raise ValueError("Enter a valid HTTP(S) link without credentials")
        return val


class ClaimCreate(BaseModel):
    statement: str = Field(min_length=8, max_length=2000)
    evidence_status: str = Field(default="unverified", pattern=r"^(unverified|supported|disputed)$")
    source_id: int | None = None
    limitations: str = Field(default="", max_length=3000)
    confidence_score: int = Field(default=3, ge=1, le=5)
    contrary_evidence: str = Field(default="", max_length=3000)


class RecommendationCreate(BaseModel):
    recommendation: str = Field(min_length=10, max_length=4000)
    rationale: str = Field(min_length=10, max_length=4000)
    risks: str = Field(min_length=10, max_length=4000)
    author: str = Field(default="Founder", min_length=2, max_length=120)


class CompetingProposalCreate(BaseModel):
    proposal_title: str = Field(min_length=5, max_length=200)
    proponent_summary: str = Field(min_length=10, max_length=3000)
    trade_offs: str = Field(min_length=10, max_length=3000)
    fiscal_impact: str = Field(default="", max_length=2000)
    legal_feasibility: str = Field(default="", max_length=2000)


class ApproveRequest(BaseModel):
    confirmed_human_review: bool


class DraftRequest(BaseModel):
    confirmed_external_ai_transfer: bool = False


class SaveSimulationRequest(BaseModel):
    model_type: str = Field(pattern=r"^(debt_sustainability|development_allocation|cross_domain_macro)$")
    scenario_name: str = Field(min_length=3, max_length=100)
    parameters: dict
    results: dict


# ---------------------------------------------------------
# Web Dashboard & Static Endpoints
# ---------------------------------------------------------

@app.get("/", include_in_schema=False)
def index():
    html_file = ROOT / "ggisp" / "index.html"
    if not html_file.exists():
        html_file = ROOT / "index.html"
    return FileResponse(html_file)


@app.get("/api/health")
def health():
    return {
        "status": "operational",
        "version": "0.2.0",
        "domains_count": 13,
        "database": "sqlite3_ready",
        "human_authority_gate": "active",
    }


# ---------------------------------------------------------
# 13 Specialist Research Divisions
# ---------------------------------------------------------

@app.get("/api/domains")
def domains():
    with db() as con:
        rows = con.execute("""
            SELECT d.*, COUNT(p.id) AS project_count
            FROM domains d LEFT JOIN projects p ON p.domain_slug=d.slug
            GROUP BY d.slug ORDER BY d.rowid
        """).fetchall()
    return [serialize(r) for r in rows]


# ---------------------------------------------------------
# Research Projects Management
# ---------------------------------------------------------

@app.get("/api/projects")
def projects():
    with db() as con:
        rows = con.execute("""
            SELECT p.*, d.name AS domain_name, d.family
            FROM projects p
            JOIN domains d ON d.slug = p.domain_slug
            ORDER BY p.id DESC
        """).fetchall()
    return [serialize(r) for r in rows]


@app.post("/api/projects", status_code=201)
def project_create(data: ProjectCreate):
    with db() as con:
        exists = con.execute("SELECT 1 FROM domains WHERE slug=?", (data.domain_slug,)).fetchone()
        if exists is None:
            raise HTTPException(400, "Unknown specialist division")
        cur = con.execute(
            "INSERT INTO projects (domain_slug, title, problem, country_code) VALUES (?, ?, ?, ?)",
            (data.domain_slug, data.title, data.problem, data.country_code.upper()),
        )
        pid = cur.lastrowid
        audit(con, pid, "create", "project", pid, f"Created project: {data.title}")
    return {"id": pid, "status": "concept", "country_code": data.country_code.upper()}


@app.get("/api/projects/{project_id}")
def project_detail(project_id: int):
    with db() as con:
        p_row = ensure_project(con, project_id)
        p = serialize(p_row)

        # Domain metadata
        dom = con.execute("SELECT * FROM domains WHERE slug=?", (p["domain_slug"],)).fetchone()
        p["domain_meta"] = serialize(dom)

        for table in ("sources", "claims", "recommendations", "competing_proposals", "simulations", "ai_drafts"):
            p[table] = [serialize(r) for r in con.execute(
                f"SELECT * FROM {table} WHERE project_id=? ORDER BY id DESC", (project_id,)
            ).fetchall()]

        p["audit_log"] = [serialize(r) for r in con.execute(
            "SELECT * FROM audit_log WHERE project_id=? ORDER BY id DESC LIMIT 50", (project_id,)
        ).fetchall()]

    return p


# ---------------------------------------------------------
# Evidence Sources & Cryptographic Provenance
# ---------------------------------------------------------

@app.post("/api/projects/{project_id}/sources", status_code=201)
def source_create(project_id: int, data: SourceCreate):
    with db() as con:
        ensure_project(con, project_id)
        # Compute SHA-256 hash snapshot of citation metadata and notes
        content_for_hash = f"{data.title}|{data.publisher}|{data.url}|{data.notes}"
        content_hash = calculate_hash(content_for_hash)

        cur = con.execute("""
            INSERT INTO sources
            (project_id, title, url, publisher, publication_year, doi, content_hash, notes, manually_reviewed, quality_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, data.title, data.url, data.publisher, data.publication_year,
            data.doi, content_hash, data.notes, int(data.manually_reviewed), data.quality_rating
        ))
        con.execute("UPDATE projects SET status='research' WHERE id=? AND status='concept'", (project_id,))
        audit(con, project_id, "create_source", "source", cur.lastrowid, f"Added source: {data.title}")
    return {"id": cur.lastrowid, "content_hash": content_hash}


# ---------------------------------------------------------
# Empirical Claims & Epistemic Uncertainty
# ---------------------------------------------------------

@app.post("/api/projects/{project_id}/claims", status_code=201)
def claim_create(project_id: int, data: ClaimCreate):
    with db() as con:
        ensure_project(con, project_id)
        source = None
        if data.source_id is not None:
            source = con.execute(
                "SELECT * FROM sources WHERE id=? AND project_id=?", (data.source_id, project_id)
            ).fetchone()
            if source is None:
                raise HTTPException(400, "Source is not associated with this project")

        if data.evidence_status == "supported" and (source is None or not source["manually_reviewed"]):
            raise HTTPException(400, "A supported claim requires a source you have manually reviewed")

        cur = con.execute("""
            INSERT INTO claims
            (project_id, statement, evidence_status, source_id, limitations, confidence_score, contrary_evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, data.statement, data.evidence_status, data.source_id,
            data.limitations, data.confidence_score, data.contrary_evidence
        ))
        audit(con, project_id, "create_claim", "claim", cur.lastrowid, f"Claim status: {data.evidence_status}")
    return {"id": cur.lastrowid, "evidence_status": data.evidence_status}


# ---------------------------------------------------------
# Competing Policy Proposals
# ---------------------------------------------------------

@app.post("/api/projects/{project_id}/competing-proposals", status_code=201)
def competing_proposal_create(project_id: int, data: CompetingProposalCreate):
    with db() as con:
        ensure_project(con, project_id)
        cur = con.execute("""
            INSERT INTO competing_proposals
            (project_id, proposal_title, proponent_summary, trade_offs, fiscal_impact, legal_feasibility)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project_id, data.proposal_title, data.proponent_summary,
            data.trade_offs, data.fiscal_impact, data.legal_feasibility
        ))
        audit(con, project_id, "create_proposal", "competing_proposal", cur.lastrowid, data.proposal_title)
    return {"id": cur.lastrowid}


# ---------------------------------------------------------
# Founder's Advisory Centre & Human Approval Gate
# ---------------------------------------------------------

@app.post("/api/projects/{project_id}/recommendations", status_code=201)
def recommendation_create(project_id: int, data: RecommendationCreate):
    with db() as con:
        ensure_project(con, project_id)
        cur = con.execute("""
            INSERT INTO recommendations
            (project_id, recommendation, rationale, risks, author)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, data.recommendation, data.rationale, data.risks, data.author))
        con.execute(
            "UPDATE projects SET status='review' WHERE id=? AND status IN ('concept', 'research')", (project_id,)
        )
        audit(con, project_id, "create_recommendation", "recommendation", cur.lastrowid, f"Author: {data.author}")
    return {"id": cur.lastrowid, "approval_status": "draft", "author": data.author}


@app.post("/api/recommendations/{recommendation_id}/approve")
def approve(recommendation_id: int, data: ApproveRequest):
    if not data.confirmed_human_review:
        raise HTTPException(400, "Approval requires explicit human review confirmation")

    with db() as con:
        rec = con.execute("SELECT * FROM recommendations WHERE id=?", (recommendation_id,)).fetchone()
        if rec is None:
            raise HTTPException(404, "Recommendation not found")

        if rec["approval_status"] == "approved":
            return {"id": recommendation_id, "approval_status": "approved"}

        pid = rec["project_id"]
        evidence_count = con.execute("""
            SELECT COUNT(*) FROM claims c
            JOIN sources s ON s.id=c.source_id
            WHERE c.project_id=? AND c.evidence_status='supported' AND s.manually_reviewed=1
        """, (pid,)).fetchone()[0]

        if evidence_count < 1:
            raise HTTPException(
                400, "Add at least one sourced, manually reviewed claim before founder approval"
            )

        con.execute(
            "UPDATE recommendations SET approval_status='approved', approved_at=datetime('now') WHERE id=?",
            (recommendation_id,),
        )
        con.execute("UPDATE projects SET status='ready' WHERE id=?", (pid,))
        audit(con, pid, "human_approve", "recommendation", recommendation_id, "Confirmed founder review")

    return {
        "id": recommendation_id,
        "approval_status": "approved",
        "warning": "Founder approval, NOT third-party verification or institutional endorsement.",
    }


# ---------------------------------------------------------
# Official Multilateral Data Hub (World Bank, IMF, WTO)
# ---------------------------------------------------------

@app.get("/api/external-data/countries")
def get_supported_countries():
    return data_service.list_supported_countries()


@app.get("/api/external-data/profile/{country_code}")
def get_country_macro_profile(country_code: str):
    try:
        return data_service.get_unified_macro_profile(country_code)
    except Exception as e:
        logger.exception("Failed to build macro profile for %s", country_code)
        raise HTTPException(502, f"Failed to retrieve official data for {country_code}: {str(e)}")


@app.get("/api/external-data/world-bank/{country_code}/{indicator_code}")
def get_world_bank_indicator(country_code: str, indicator_code: str):
    return data_service.world_bank.fetch_indicator(country_code, indicator_code)


@app.get("/api/external-data/imf/{country_code}")
def get_imf_profile(country_code: str):
    return data_service.imf.get_country_fiscal_profile(country_code)


@app.get("/api/external-data/wto/{country_code}")
def get_wto_profile(country_code: str):
    return data_service.wto.get_trade_profile(country_code)


# ---------------------------------------------------------
# Quantitative Policy Modelling Laboratory
# ---------------------------------------------------------

@app.post("/api/modelling/debt/simulate")
@app.post("/api/debt/simulate")  # Backwards compatibility with v0.1
def simulate_sovereign_debt(data: DynamicDebtAssumptions):
    return simulate_debt(data)


@app.post("/api/modelling/development-finance/simulate")
def simulate_development_finance(data: DevelopmentFinanceAssumptions):
    return simulate_development_allocation(data)


@app.post("/api/modelling/cross-domain/simulate")
def simulate_cross_domain_model(data: CrossDomainAssumptions):
    return simulate_cross_domain(data)


@app.post("/api/projects/{project_id}/save-simulation")
def save_simulation(project_id: int, data: SaveSimulationRequest):
    with db() as con:
        ensure_project(con, project_id)
        cur = con.execute("""
            INSERT INTO simulations (project_id, model_type, scenario_name, parameters_json, results_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_id, data.model_type, data.scenario_name,
            json.dumps(data.parameters), json.dumps(data.results)
        ))
        audit(con, project_id, "save_simulation", "simulation", cur.lastrowid, data.scenario_name)
    return {"id": cur.lastrowid, "status": "saved"}


# ---------------------------------------------------------
# AI Research Assistant (Segregated & Safeguarded)
# ---------------------------------------------------------

@app.post("/api/projects/{project_id}/ai-draft")
def make_ai_draft(project_id: int, data: DraftRequest):
    try:
        return run_ai_draft(project_id, confirmed_transfer=data.confirmed_external_ai_transfer)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.exception("AI drafting failed")
        raise HTTPException(502, "AI drafting encountered an error. Check configuration and connectivity.")


# ---------------------------------------------------------
# Structured Policy Brief Export
# ---------------------------------------------------------

@app.get("/api/projects/{project_id}/brief.md")
def export_brief(project_id: int):
    try:
        content = generate_markdown_brief(project_id)
        return PlainTextResponse(
            content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="ggisp-policy-brief-{project_id}.md"'},
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
