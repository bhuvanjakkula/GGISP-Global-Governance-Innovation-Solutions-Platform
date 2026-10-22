"""Policy Brief Generator converting research, evidence, and quantitative models into structured briefs."""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from ggisp.db import db


def generate_markdown_brief(project_id: int) -> str:
    """Generate a comprehensive, reviewable Markdown policy brief."""
    with db() as con:
        p = con.execute("""
            SELECT p.*, d.name AS domain_name, d.lead_institution, d.family
            FROM projects p JOIN domains d ON d.slug=p.domain_slug
            WHERE p.id=?
        """, (project_id,)).fetchone()
        if not p:
            raise ValueError("Project not found")

        sources = [dict(r) for r in con.execute("SELECT * FROM sources WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]
        claims = [dict(r) for r in con.execute("SELECT * FROM claims WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]
        recs = [dict(r) for r in con.execute("SELECT * FROM recommendations WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]
        proposals = [dict(r) for r in con.execute("SELECT * FROM competing_proposals WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]
        sims = [dict(r) for r in con.execute("SELECT * FROM simulations WHERE project_id=? ORDER BY id DESC LIMIT 5", (project_id,)).fetchall()]
        audit = [dict(r) for r in con.execute("SELECT * FROM audit_log WHERE project_id=? ORDER BY id DESC LIMIT 15", (project_id,)).fetchall()]

    lines = [
        f"# GGISP Policy Research Brief: {p['title']}",
        "",
        "> **DOCUMENT CLASSIFICATION:** INTERNAL RESEARCH & EVIDENCE DOSSIER  ",
        f"> **Specialist Division:** {p['domain_name']} (`{p['domain_slug']}`) | **Family:** {p['family'].title()}  ",
        f"> **Reference Institution:** {p['lead_institution']} | **Target Country:** {p['country_code'] or 'Global'}  ",
        f"> **Lifecycle Status:** {p['status'].upper()} | **Platform Version:** GGISP v0.2.0  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Policy Problem",
        p["problem"],
        "",
        "---",
        "",
        "## 2. Multilateral Evidence Register",
        "Empirical sources cataloged in the shared research database with cryptographic SHA-256 provenance hashes:",
        "",
    ]

    if not sources:
        lines.append("*No sources logged. Conclusions in this brief cannot be treated as evidence-backed.*")
    else:
        for s in sources:
            rev_label = "✅ Founder Examined" if s["manually_reviewed"] else "⚠️ Unverified Record"
            quality = s["quality_rating"].upper() if "quality_rating" in s.keys() else "STANDARD"
            doi_str = f" | DOI: `{s['doi']}`" if s.get("doi") else ""
            hash_str = f" | SHA-256: `{s['content_hash'][:16]}...`" if s.get("content_hash") else ""
            lines.extend([
                f"### [S{s['id']}] {s['publisher']} — {s['title']}",
                f"- **Publisher / Authority:** {s['publisher']} (Year: {s.get('publication_year') or 'N/A'}){doi_str}",
                f"- **Source URL:** {s['url']}",
                f"- **Review Status:** {rev_label} | **Evidence Quality:** {quality}{hash_str}",
                f"- **Logged Date:** {s['accessed_at']}",
            ])
            if s["notes"]:
                lines.append(f"- **Analyst Research Notes:** {s['notes']}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Empirical Claims & Epistemic Uncertainties",
        "Specific factual propositions evaluated against recorded sources:",
        "",
    ])

    if not claims:
        lines.append("*No research claims recorded for this project.*")
    else:
        for c in claims:
            status_tag = c["evidence_status"].upper()
            src_ref = f"[S{c['source_id']}]" if c["source_id"] else "None (Unlinked)"
            conf = f"{c.get('confidence_score', 3)}/5"
            lines.extend([
                f"#### Claim C{c['id']} `[{status_tag}]` (Confidence: {conf})",
                f"**Statement:** {c['statement']}",
                f"- **Evidentiary Basis:** Linked Source {src_ref}",
                f"- **Known Analytical Limitations:** {c['limitations'] or 'None specified'}",
            ])
            if c.get("contrary_evidence"):
                lines.append(f"- **Contrary Evidence / Competing Findings:** {c['contrary_evidence']}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Competing Policy Proposals & Structural Trade-offs",
        "Independent comparative policy options analyzed before formal recommendations:",
        "",
    ])

    if not proposals:
        lines.append("*No alternative proposals registered. Orthodox policy counterfactuals should be documented.*")
    else:
        for pr in proposals:
            lines.extend([
                f"### Alternative: {pr['proposal_title']}",
                f"- **Proponents & Summary:** {pr['proponent_summary']}",
                f"- **Trade-offs & Unintended Consequences:** {pr['trade_offs']}",
                f"- **Fiscal Impact:** {pr.get('fiscal_impact') or 'Not assessed'}",
                f"- **Legal & Institutional Feasibility:** {pr.get('legal_feasibility') or 'Not assessed'}",
                "",
            ])

    lines.extend([
        "---",
        "",
        "## 5. Quantitative Policy Simulations",
        "Mathematical and empirical model calculations recorded for this dossier:",
        "",
    ])

    if not sims:
        lines.append("*No recorded simulations on file. Run the Sovereign Debt or Cross-Domain models in the laboratory.*")
    else:
        for sim in sims:
            lines.extend([
                f"### Model: {sim['model_type'].replace('_', ' ').title()} (`{sim['scenario_name']}`)",
                f"- **Run Timestamp:** {sim['run_at']}",
                f"```json",
                f"{json.dumps(json.loads(sim['results_json']), indent=2)[:800]}...",
                f"```",
                "",
            ])

    lines.extend([
        "---",
        "",
        "## 6. Founder-Authored Policy Guidance",
        "Personally authored guidance by the platform founder. Distinct from AI suggestions and requiring strict evidentiary gates for approval:",
        "",
    ])

    if not recs:
        lines.append("*No founder-authored recommendations recorded.*")
    else:
        for r in recs:
            app_status = r["approval_status"].upper()
            app_date = r["approved_at"] or "Pending independent human review"
            lines.extend([
                f"### Recommendation R{r['id']}: [{app_status}] — Author: {r['author']}",
                f"**Actionable Recommendation:**",
                f"> {r['recommendation']}",
                "",
                f"**Causal Mechanism & Rationale:**",
                f"{r['rationale']}",
                "",
                f"**Risks, Uncertainty & Mitigations:**",
                f"{r['risks']}",
                "",
                f"**Approval Audit:** {app_status} on {app_date}",
                "",
            ])

    # Append Decision Lab scenario comparisons if available
    try:
        from ggisp.lab import runs as lab_runs, run_detail as lab_run_detail
        saved_runs = lab_runs(project_id)
        if saved_runs:
            lines.extend(["---", "", "## 7. Saved Decision Laboratory Scenario Comparisons", ""])
            for saved in saved_runs:
                rd = lab_run_detail(saved["id"])
                lines.extend([
                    f"### Run {saved['id']}: {saved['name']}",
                    f"- **Model Version:** `{saved['model_version']}` | **SHA-256 Digest:** `{saved['sha256']}`",
                    f"- **Inputs:** `{json.dumps(rd['inputs'], sort_keys=True)}`",
                    f"- **Terminal Summary:** `{json.dumps(rd['outputs']['summary'], sort_keys=True)}`",
                    f"- **Limitations:** {rd['outputs'].get('limitations', 'N/A')}",
                    "",
                ])
    except Exception:
        pass

    # Append Workbench multi-domain studies and exact evidence spans
    try:
        from ggisp.workbench import brief_sections
        wb_sections = brief_sections(project_id)
        if wb_sections:
            lines.extend(["---"])
            lines.extend(wb_sections)
            lines.extend([""])
    except Exception:
        pass

    lines.extend([
        "---",
        "",
        "## 7. Institutional Submission & Governance Checklist",
        "Mandatory verification steps required before transmission to international institutions (e.g., IMF, World Bank, WTO, UN):",
        "",
        "- [ ] **Primary Source Attestation:** Every empirical claim has been verified against published official documentation or peer-reviewed literature.",
        "- [ ] **Mathematical Integrity:** Equations, parameter bounds, and assumptions are fully transparent and independently checkable.",
        "- [ ] **Human Authority Principle:** All policy guidance is explicitly attributed to human authors; no AI drafts have been presented as approved advice.",
        "- [ ] **NIST AI Risk Management Framework Compliance:** Model bias, hallucination boundaries, and data provenance are documented.",
        "- [ ] **Independent Subject Review:** Written review obtained from at least one recognized external sector specialist.",
        "- [ ] **Diplomatic Clearance:** No classified, non-public, or sensitive sovereign intelligence is contained in this document.",
        "",
        "---",
        "*Generated automatically by GGISP Platform v0.2.0 • Local-First Research Engine*",
    ])

    return "\n".join(lines)
