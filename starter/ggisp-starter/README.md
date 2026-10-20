# GGISP — Global Governance, Innovation & Solutions Platform

**Local-first research prototype, v0.1 — October 2026**

A small working implementation of a 13-domain international research and advisory workspace. It is an independent research tool, not a UN platform, validated policy engine, diplomatic communication tool, or production-safe public website.

## What actually works

- Browser dashboard listing 13 international policy divisions.
- Create research projects and define their policy questions.
- Record source URLs, publishers, research notes and manual-review attestations.
- Add research claims with evidence status and linked sources.
- Write founder-authored policy recommendations, separately from AI-generated text.
- Human-confirmed founder approval after at least one source-backed claim has been reviewed.
- Illustrative debt-to-GDP scenario simulation using a clearly specified equation.
- Download a Markdown research/policy brief that displays source status, uncertainties, draft/approved recommendation status and review checklist.
- Optionally generate unverified AI working notes from the project's user-entered context using an externally configured API key.
- Audit log entries for changes and founder approvals.

## Quick start (Python 3.10+)

```bash
# Unzip and navigate into the project folder
cd ggisp-starter
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn ggisp.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000** in your browser. FastAPI API docs are available at **http://127.0.0.1:8000/docs**. The local SQLite database is created in `data/ggisp.db`. The demo project contains *no real claims or verified sources*.

### Test the app

```bash
pip install -r requirements-dev.txt
pytest -q
```

### Optional AI drafting (external service, charges may apply)

The software works **without** an AI key. If you wish to enable a provider-supported AI drafting experiment, set `OPENAI_API_KEY` as a server environment variable, and optionally `GGISP_AI_MODEL` to a model accessible to your account. The default is only a configurable sample model string, not a guarantee of access.

On Linux/macOS:

```bash
export OPENAI_API_KEY='your-key-here'
export GGISP_AI_MODEL='gpt-5.5'
```

On PowerShell:

```powershell
$env:OPENAI_API_KEY = 'your-key-here'
$env:GGISP_AI_MODEL = 'gpt-5.5'
```

**Never place credentials in a browser, repository or policy report.** The AI action requests an explicit confirmation before transferring source notes, claims and project problem statements to an external service. These are user-entered notes; the app does not retrieve or verify the contents of source URLs, and its instructions cannot guarantee the absence of model error. AI-generated drafts remain labeled and unapproved. API usage has separate pricing and terms.

## A concrete first study

1. Open the demonstration sovereign-debt project.
2. Run the model using the prefilled *fictional* assumptions, and then vary the interest or growth input.
3. Create a precise research claim about how the model responds; identify it explicitly as a mathematical illustration rather than an actual-country forecast.
4. Add a credible primary source and manually review the publication.
5. Write a founder recommendation that states the mechanism, risk and uncertainty.
6. Export the brief, obtain independent expert review, and revise before any institutional contact.

## Limitations and deployment warning

- **Do not deploy publicly:** there is no user authentication, role-based authorization, rate limiting, CSRF protection, encrypted database, tenant separation, secure file upload, or production monitoring.
- **Manual-review attestations are NOT third-party verification.** A reviewer can mistakenly mark an unsuitable source reviewed. Likewise, one supported claim is an intentionally minimal workflow gate, not sufficient validation for important diplomatic or financial proposals.
- The scenario equation omits exchange-rate effects, contingent liabilities, debt composition, stock-flow adjustments, bargaining constraints and model uncertainty.
- There is no autonomous data collection, no connection to international leadership, and no institutional submission. URLs are merely recorded, not fetched.
- Local project notes are kept in an ordinary unencrypted SQLite file. Do not insert confidential, classified, identifying, health or sensitive national-security information.
- There are no offensive cybersecurity, nuclear-control, or military operations capabilities.

## References and model standards

- FastAPI: https://fastapi.tiangolo.com/tutorial/first-steps/
- World Bank Indicators API: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api
- WTO Developer Portal: https://apiportal.wto.org/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- OpenAI Python API documentation (optional adapter): https://developers.openai.com/api/reference/python

See `SPECIFICATION.md` for next-phase milestones, normalized entities, acceptance criteria and research governance.
