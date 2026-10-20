# GGISP: Functional & Technical Specification

Version 0.1 | Concept-stage baseline | 20 October 2026

## 1. Problem and proposed value

GGISP is a local-first international policy research workspace. Its intended users are the independent founder/researcher, future subject matter reviewers, and eventually collaborating institutions. The platform does **not** make diplomatic decisions. It organizes evidence, models alternatives, records authored recommendations, and creates reviewable outputs.

### Decision boundaries

- The founder controls all research topics and authored advisory statements.
- AI drafts are explicitly labeled **AI-generated / unverified / not approved**; they cannot be automatically promoted to recommendations.
- Source URLs and notes are researcher-entered; adding a URL does not authenticate its content.
- A supported claim can be logged only when linked to a manually examined source.
- Founder approval requires a human confirmation and at least one reviewed supported claim. This is a workflow check only, **not external validation**.
- No classified, secret, military operational, personal health, or confidential diplomatic data is suitable for the prototype.

## 2. Scope and measurable acceptance criteria

| ID | Capability | Acceptance test | Status |
|----|------------|-----------------|--------|
| F01 | Browse 13 policy domains | `GET /api/domains` gives exactly 13 entries | Implemented |
| F02 | Create a project | POST valid domain, title and research question; project persists | Implemented |
| F03 | Curate sources | Save title, publisher, URL, notes and human review flag | Implemented |
| F04 | Record claims | 'supported' requires manually reviewed linked source | Implemented |
| F05 | Document advice | Record founder-authored recommendation, rationale, risks | Implemented |
| F06 | Human approval | Block approval without reviewed supported claim; write audit entry | Implemented |
| F07 | Illustrative debt model | Input five parameters; return baseline plus yearly debt ratios | Implemented |
| F08 | Export brief | File includes research question, sources, claim labels, author and risk notes | Implemented |
| F09 | AI drafting | Opt-in external AI call only with server key; mark as unverified | Optional, implemented |
| F10 | Reliable external data updates | Scheduled and tested import for World Bank/IMF/WTO datasets | Not implemented |
| F11 | Independent citation verification | Verify source pages, dates, licensing and claim context | Not implemented |
| F12 | Multiuser organization | Authentication, role management, encrypted storage, release reviews | Not implemented |
| F13 | External institutional submission | Human-authorized, logged and recipient-specific submission workflows | Not implemented |
| F14 | Cross-domain models | Evaluate joint effects of trade, debt, development finance | Not implemented |

The sample project contains an **illustrative hypothetical problem**, not factual claims about any particular country.

## 3. Thirteen-module domain architecture

All modules share core tables and approval mechanisms; specialized engines should be added only after data and review readiness.

| Division | Example V2 output | Required expert validation |
|----------|-------------------|----------------------------|
| Nuclear security | Non-operational safeguards and verification policy mapping | Arms-control lawyers, safety specialists |
| UN Security Council | Charter and reform-option comparison matrix | UN law and diplomacy experts |
| WTO and global trade | Tariff and legal dispute comparisons | Trade lawyers and economists |
| Sovereign debt | Bounded debt sustainability scenario comparisons | Sovereign debt economists |
| AI governance | Risks and assurance evidence register | AI safety, ethics, ML specialists |
| Cybersecurity | Defensive control and incident cooperation mapping | Defensive cybersecurity experts |
| Global health | Public-health funding or supply coordination analysis | Public-health specialists, privacy counsel |
| Space security | Debris and civilian satellite collision policy options | Space operators and space-law advisers |
| Critical minerals | Source concentration and chain-of-custody summaries | Supply-chain and environmental experts |
| Ocean governance | Marine protection, fisheries and ocean treaty tracking | Marine scientists and UNCLOS specialists |
| International taxation | International tax rules and cross-border simulation | International taxation experts |
| Development finance | Project prioritization and impact assessment | Development economists and finance specialists |
| Climate finance | Funding gap and adaptation policy comparisons | Climate scientists and adaptation finance advisers |

## 4. Technical architecture (prototype)

```text
Browser (HTML/CSS/JS)
  |
  +---- HTTP localhost 127.0.0.1
           |
           FastAPI application /api/*
           |         |             |
           |         |             +-- Optional opt-in external AI Responses API
           |         +-- Deterministic illustrative debt calculation (no LLM)
           +-- sqlite3 local DB (data/ggisp.db)
                   |-- 13 domains
                   |-- project registry
                   |-- evidence sources
                   |-- claims and source associations
                   |-- founder recommendations and approvals
                   |-- unverified AI drafts
                   +-- simple audit log
```

### Code tree

```text
ggisp-starter/
├── README.md                # Setup and caveats
├── SPECIFICATION.md         # This document
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── ggisp/
│   ├── __init__.py
│   ├── db.py                # SQLite schema, catalog and seeding
│   ├── main.py              # FastAPI endpoints and gating
│   ├── modelling.py         # Transparent debt-ratio calculation
│   └── index.html           # Local browser UI
├── data/                    # Runtime SQLite database (gitignored)
└── tests/
    └── test_app.py          # Functional and guardrail tests
```

### Entities and provenance

- `domains(slug, name, description, family)`
- `projects(id, domain_slug, title, problem, status, created_at)`
- `sources(id, project_id, title, url, publisher, notes, manually_reviewed, accessed_at)`
- `claims(id, project_id, statement, evidence_status, source_id, limitations, created_at)`
- `recommendations(id, project_id, recommendation, rationale, risks, author, approval_status, created_at, approved_at)`
- `ai_drafts(id, project_id, output_text, model, created_at)`
- `audit_log(id, project_id, action, record_type, record_id, happened_at)`

Future schema must add source snapshot/checksum, actual publication date, evidence strength rubric, researcher identity, review chain, provenance document identifier, DOI, confidence intervals, reviewer sign-off, version history and publication states.

### Public API for local prototype

| Method | Route | Function |
|--------|-------|----------|
| GET | `/api/domains` | List 13 modules |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Project details, records and audit trail |
| POST | `/api/projects/{id}/sources` | Store source metadata |
| POST | `/api/projects/{id}/claims` | Store evidence-rated claim |
| POST | `/api/projects/{id}/recommendations` | Save founder-authored advice |
| POST | `/api/recommendations/{id}/approve` | Founder review confirmation |
| POST | `/api/debt/simulate` | Illustrative debt ratio path |
| POST | `/api/projects/{id}/ai-draft` | Optional AI-generated working note |
| GET | `/api/projects/{id}/brief.md` | Download Markdown policy research brief |

## 5. Research-to-policy workflow

**Question → Sources → Claim evaluation → Modelling → Alternatives → Human-authored recommendation → Independent review → Release**

1. **Define:** Specify one research question with relevant stakeholders, jurisdiction and time period.
2. **Source:** Prioritize primary international-organization data, treaties, decisions, laws and peer-reviewed research. Log URL, publisher, date, license, and retrieved copy (later phase).
3. **Evaluate:** Each empirical claim links to a source and lists uncertainty, contrary evidence and evidentiary limits.
4. **Model:** Run transparent numerical tests with explicit assumptions. Compare baseline, policy counterfactual and stress cases. Do not label deterministic outputs as forecasts.
5. **Deliberate:** Develop at least two contrasting feasible policies, affected parties, distributional impacts, costs, legal issues and security implications.
6. **Author:** Founder composes an original recommendation and its mechanism. AI assistance is segregated in a separate record.
7. **Review:** Obtain relevant technical, legal, ethics, security and domain expert review proportionate to stakes.
8. **Publish:** Assign version, review date, sources and disclaimers; submit to the **appropriate institution only after checking its rules**. Capture feedback and update.

### Sample pilot research question

*Under illustrative scenarios, how do changes in interest rates, nominal GDP growth and primary fiscal balances affect public debt relative to GDP?*

Equation:

```text
Next debt ratio = current debt ratio * (1 + nominal interest rate)
                  / (1 + nominal GDP growth rate)
                  - primary budget surplus (in % GDP points)
```

This equation is **not** a complete sovereign debt sustainability framework, is not validated for any country, and omits multiple crucial mechanisms. Use it only as a simple demonstration of transparent and reproducible policy modelling.

## 6. V2 architecture decisions

| Concern | Prototype | Production direction |
|---------|-----------|----------------------|
| Frontend | Simple HTML/JS | React/Next.js with accessibility and test coverage |
| API | FastAPI | FastAPI with auth, policy and rate-limit middleware |
| Data storage | SQLite | PostgreSQL, row-level security, encryption and backups |
| Search | None | Document ingestion with searchable, versioned evidence corpus |
| AI | Optional external text draft | Provider-agnostic RAG with evaluation dataset and traceable quotations |
| Models | Transparent debt-ratio equation | Validated domain-specific quantitative models |
| Provenance | User source links and review flag | Snapshot/hash/date, citation spans, bias and quality checks |
| Identity | Single local researcher | Role-based founder/researcher/reviewer/publisher control |
| Governance | Manual gate | Two-person independent signoff and conflict-of-interest disclosure |
| International submission | Manual export only | Authorized, reviewable routing/approval records |

### Security constraints before public deployment

- Authentication, authorization, CSRF protections, secure session management and rate limiting.
- Encrypted storage and backups, reliable incident monitoring, logging and recovery processes.
- AI prompt-injection containment, data minimization, retention/deletion policy and external transmission consent.
- Primary-data licensing review, citation checking, scientific reproducibility and validation evidence.
- Strict restriction of any military, nuclear or cyber module to lawful, non-operational, defensive/peaceful policy analysis.
- Human adjudication for all public or high-stakes outputs; no independent decisions on nuclear systems, international negotiations, or financial commitments.

## 7. Milestone roadmap (indicative only)

| Milestone | What to achieve | Evidence of completion |
|-----------|-----------------|------------------------|
| M0 Local prototype | Install, run, inspect 13 divisions | App works on a laptop and tests pass |
| M1 First research dossier | One well-defined debt research question, 5–10 qualified sources | Exported evidence register and uncertainty notes |
| M2 Model methodology | Baseline, counterfactual and stress tests with peer-checkable calculations | Technical methods note and test cases |
| M3 Author's recommendation | 2+ competing options, founder guidance, risk treatment | Attributed policy brief with traceable sources |
| M4 External review | At least one relevant independent subject expert | Written review and change log |
| M5 Module expansion | WTO + development-finance datasets and comparators | Reproducible multi-domain demo |
| M6 Institutional dialogue | Approach relevant legitimate consultation and research channels | Feedback documented, without assuming acceptance |

M0 implementation is delivered. M1–M6 depend on founder research, external expertise and available resources and cannot be responsibly guaranteed on fixed dates.

## 8. Responsible metrics

Track: proportion of statements linked to reviewed primary sources, number of outstanding uncertainties, reproducibility of models, elapsed time to correction, independent-review findings, security incidents, and whether recipients respond or invite formal follow-up.

Do **not** present `founder-approved` as `scientifically proven`, `legally binding`, or `endorsed by the UN`.

## 9. Trusted starting references

- FastAPI, First Steps: https://fastapi.tiangolo.com/tutorial/first-steps/
- World Bank Indicators API: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api
- WTO Developer Portal: https://apiportal.wto.org/
- IMF Data: https://data.imf.org/
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- OpenAI Python reference (optional): https://developers.openai.com/api/reference/python
