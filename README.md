# GGISP — Global Governance, Innovation & Solutions Platform
**Platform Version 0.2.0 — October 2026**

A unified international research, evidence verification, and policy innovation platform combining mathematical models, official multilateral data, and personally authored policy guidance.

---

## 1. Core Platform Capabilities

1. **Global Issues Dashboard:** Complete coverage of **13 international policy divisions** (Nuclear Security, UN Security Council, WTO & Global Trade, Sovereign Debt, AI Governance, Cybersecurity, Global Health, Space Security, Critical Minerals, Ocean Governance, International Taxation, Development Finance, and Climate Finance).
2. **Official Multilateral Data Hub:** Live connections and authenticated benchmark profiles for **World Bank Open Indicators API**, **IMF World Economic Outlook (WEO)**, and **WTO World Tariff Profiles**.
3. **Quantitative Policy Modelling Laboratory:**
   - **Model 1: Dynamic Sovereign Debt Sustainability Model** with currency depreciation sensitivities, contingent liability shocks, and stabilizing primary balances.
   - **Model 2: Concessional Development Finance Allocation Engine** optimizing capital across Infrastructure, Health, Education, and Climate Adaptation subject to revenue absorption constraints.
   - **Model 3: Validated Cross-Domain Macro-Fiscal Simulator** evaluating the joint impacts of WTO tariff shocks, debt trajectories, and concessional MDB capital across 3 comparative policy paths.
4. **Human Authority & Sourced Claims Engine:**
   - Strict Human Authority Gate: AI drafts cannot be automatically promoted to approved recommendations.
   - Founder approval requires personal human review attestation and at least one manually examined source and supported empirical claim.
   - Evidence records calculate cryptographic **SHA-256 hashes** for verifiable data provenance.
5. **AI Research Assistant (Segregated & Safeguarded):**
   - Explicit user consent gate required prior to data transfer.
   - Built-in local intelligent heuristic synthesis engine that operates offline without paid API keys.
   - Optional external LLM adapter (OpenAI Responses / Chat API) with strict prompt-injection containment.
6. **Policy Brief Generator:**
   - Generates and exports comprehensive Markdown dossiers formatted for institutional submission (World Bank, IMF, WTO, UN), complete with evidence chains, mathematical models, competing proposals, and submission checklists.
7. **Audit Trail:**
   - Complete database audit logging for all record creations, simulation archives, and human review approvals.

---

## 2. Quick Start

### Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.14)
- Web browser (Chrome, Edge, Firefox, Safari)

### Installation & Run

```powershell
# Open terminal in project root
cd C:\Users\bhuva\.gemini\antigravity-ide\scratch\ggisp-platform

# Install dependencies
pip install -r requirements.txt

# Run the development server
python -m uvicorn ggisp.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
- **Interactive Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 3. Automated Test Suite

All 22 automated tests verify functionality, mathematical identity equations, data connectors, and security guardrails:

```powershell
python -m pytest -v
```

Verification status:
- `tests/test_domains.py`: 13 specialist divisions and seed catalog
- `tests/test_projects_evidence.py`: Project lifecycle, HTTP(S) URL validation, SHA-256 hashing, unreviewed source barriers
- `tests/test_recommendations_approval.py`: Strict human review gate and audit logging
- `tests/test_debt_model.py`: Dynamic sovereign debt stock-flow identities and adverse shocks
- `tests/test_development_finance.py`: Multi-sector multiplier allocation and debt service absorption
- `tests/test_cross_domain_model.py`: Macro-fiscal trade shock and multilateral policy paths
- `tests/test_external_data.py`: World Bank, IMF, and WTO data connectors and caching
- `tests/test_ai_assistant.py`: Consent gate and offline heuristic fallback synthesis
- `tests/test_brief_generator.py`: Structured Markdown brief export and checklist
- `tests/test_competing_proposals.py`: Deliberation options and simulation archiving
- `tests/test_e2e_api.py`: Full end-to-end research-to-policy lifecycle

---

## 4. Docker Deployment

```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## 5. Security & Governance Standards

- **NIST AI Risk Management Framework (RMF 1.0):** Transparent distinction between AI heuristic drafts and human policy authority.
- **Data Minimization:** No classified, non-public sovereign intelligence, or confidential diplomatic secrets are handled.
- **Independent Validation Warning:** Founder approval is an internal quality gate, not third-party scientific proof or official institutional endorsement.
