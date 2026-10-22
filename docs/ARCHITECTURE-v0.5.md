# GGISP v0.5 — advanced analytical integration

The v0.4 storage, evidence, review and API architecture remains intact. Seven advanced engines extend the catalog to twenty methods without new third-party runtime packages or new database tables.

`engine_types.py` holds shared validation types and metadata, avoiding circular imports. `engines.py` retains the thirteen foundation methods and registers `advanced.py`. The advanced module implements robust discrete decision comparison, exhaustive coalition power, Wilson benchmark intervals, seeded stochastic debt, bounded residual-network maximum flow, quarter-day SEIR dynamics and contractive cross-domain influence propagation.

All engines share the same typed schema → calculate → optional save → evidence links → hash/reproduce → CSV/brief → human review flow. Existing method versions and old saved studies remain intact. New methods start at version 1.0.0 (robust-policy 1.0.1 adds explicit tie reporting), and app version is 0.5.0.

Catalog entries can declare `tier`, `applicable_domains` and `references`. The browser provides method-family/project-relevance filters and displays methodological references. Numeric arrays such as robust scenario outcomes are edited as comma-separated numeric values. Domain fields use existing division selectors. Time charts handle years or days and multiple series; SEIR shows baseline/policy infectious paths and stochastic debt shows percentile paths.

The research assistant recommends tools applicable to the project's division rather than only their primary catalog division. Robust policy choice and cross-domain propagation apply to all thirteen divisions; other specialized methods have narrower explicit applicability.

The endpoints remain `/api/engines`, `/api/engines/{id}/calculate`, `/api/projects/{id}/analyses/{engine}`, `/api/analyses/{id}/reproduce`, exports, reviews and evidence routes. `/methods` exposes the advanced method notes and thirteen-area application map. No implicit network calls, autonomous decisions or external publication were added.

Seeded stochastic results depend on the Python/runtime implementation. Study reproduction compares actual stored output against recalculated output and reports differences rather than assuming that matching seeds prove cross-version identity. Source hashes identify content; referenced evidence is still manually mapped to model inputs.

Numerical limits: at most 16 coalition players; 50 policy options × 30 scenarios; 5,000 Monte Carlo paths × 30 years; 40 flow nodes and 150 directed edges; 365 SEIR days with four transfers per day; 13 cross-impact divisions with outgoing sums ≤1 and damping ≤0.95. The graph returns convergence status. Model limitations are attached to results and policy briefs.

Research evidence and scope details are in ADVANCED-METHODS-v0.5.md. v0.4 architecture notes remain the detailed baseline for persistence, security boundaries, imports and human review. This remains single-user localhost research software.
