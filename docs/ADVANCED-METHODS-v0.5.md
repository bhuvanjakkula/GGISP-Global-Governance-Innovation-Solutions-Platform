# Advanced innovation methods — GGISP v0.5

This release adds seven executable methods to the thirteen foundation tools: twenty tools across thirteen divisions. The innovation is their integration with one evidence, reproducibility and human-review workflow. These are established mathematical techniques and explicitly defined scenario models; no new scientific discovery or independently validated policy solution is claimed.

## Technologies mapped to all thirteen areas

| Area | Practical question | Available advanced tools | Evidence and scope boundary |
|---|---|---|---|
| Nuclear security | Compare peaceful safeguards-policy options under adverse evidence and implementation scenarios. | robust-policy, cross-impact | Public safeguards evidence, independent arms-control review; no operational nuclear modeling. |
| UN Security Council | Measure how voting designs change coalition power, then compare reform options across scenarios. | voting-power, robust-policy | Hypothetical coalitions and explicit rules; no assumption that current member preferences are known. |
| WTO and trade | Stress-test trade-network capacities and compare negotiation options. | supply-network, voting-power, robust-policy | Common commodity/period units, actual capacity evidence and trade-law review. |
| Sovereign debt | Explore correlated interest/growth uncertainty and trace assumed links to development spending. | stochastic-debt, cross-impact | Country-calibrated dynamics and expert debt analysis remain required; not the IMF framework. |
| AI governance | Evaluate observed benchmark failures with uncertainty and group-specific sample sizes. | benchmark-audit, robust-policy | Independent test sets, representative groups and correlation/multiple-comparison assessment. |
| Cybersecurity | Evaluate defensive model failure rates and compare control choices under uncertain effectiveness. | benchmark-audit, robust-policy | Defensive testing only; no offensive actions or claims of zero risk. |
| Global health | Compare capacity-demand trajectories and locate resource-network bottlenecks. | health-seir, supply-network, robust-policy | Synthetic model until calibrated; public-health expert review; no patient decisions. |
| Space security | Compare civilian disposal and governance strategies under uncertain success assumptions. | robust-policy, cross-impact | Orbital propagation/collision probabilities are not implemented; realistic trajectory covariance would be required. |
| Critical minerals | Identify supply bottlenecks and quantify throughput lost to disruptions. | supply-network, robust-policy | Actual topology and capacities, alternative sourcing feasibility and time dependence need evidence. |
| Ocean governance | Compare prevention and cleanup strategies across inflow scenarios and logistics bottlenecks. | robust-policy, supply-network | Existing stock model remains closed-box; no ocean-circulation or ecological prediction. |
| International taxation | Compare policy robustness and coalition influence under different revenue-base assumptions. | robust-policy, voting-power | Current laws and behavioral estimates are not supplied or inferred. |
| Development finance | Combine the existing portfolio optimizer with scenario robustness and cross-sector impacts. | robust-policy, cross-impact, supply-network | Common benefit units and empirical effect estimates must be justified. |
| Climate finance | Compare funding and mitigation choices across uncertain fiscal and outcome scenarios. | robust-policy, stochastic-debt, cross-impact | Debt simulator is relevant only to financing assumptions, not climate physics; no calibrated climate forecasting. |

## Implemented advanced methods

### Robust policy choice under uncertainty

Engine `robust-policy` · version `1.0.1`

Compare maximin, weighted-mean and minimax-regret choices; identify Pareto-dominated options. Higher scores are better. Regret is the gap to the best option within each scenario.

Limitations: Scenario scores must share units and a common higher-is-better direction. Weights are researcher assumptions, not estimated probabilities. Robustness covers only the entered scenarios.

Applicable divisions: nuclear-security, un-security-council, wto-trade, sovereign-debt, ai-governance, cybersecurity, global-health, space-security, critical-minerals, ocean-governance, international-tax, development-finance, climate-finance

Research references:
- [World Bank: robust investment decisions](https://ppp.worldbank.org/library/making-informed-investment-decisions-uncertain-world)

Example input:
```json
{
  "scenarios": [
    {
      "name": "Favorable",
      "weight": 1
    },
    {
      "name": "Adverse",
      "weight": 1
    }
  ],
  "options": [
    {
      "name": "High upside",
      "outcomes": [
        100,
        0
      ]
    },
    {
      "name": "Resilient option",
      "outcomes": [
        65,
        55
      ]
    },
    {
      "name": "Weak option",
      "outcomes": [
        30,
        20
      ]
    }
  ]
}
```

### Coalition voting-power analysis

Engine `voting-power` · version `1.0.0`

Exhaustively count coalitions and each player's losing-to-winning swings. Report absolute and normalized Banzhaf power, respecting configured veto players.

Limitations: At most 16 hypothetical players. Coalition enumeration treats possible membership patterns symmetrically; actual preferences, negotiation dynamics and current UN procedures are not modeled.

Applicable divisions: un-security-council, wto-trade, international-tax

Research references:
- [Banzhaf: account of the voting-power method](https://www.banzhaf.net/accom.html)

Example input:
```json
{
  "players": [
    {
      "name": "Group A",
      "weight": 2,
      "veto": false
    },
    {
      "name": "Group B",
      "weight": 1,
      "veto": false
    },
    {
      "name": "Group C",
      "weight": 1,
      "veto": false
    }
  ],
  "quota": 3
}
```

### AI benchmark uncertainty and group audit

Engine `benchmark-audit` · version `1.0.0`

Compute observed failure rates and two-sided 95% Wilson score intervals per group; compare interval upper bounds to a chosen tolerance. Show observed group-rate gap.

Limitations: Intervals assume independent binomial trials. They do not cover dataset shift, clustered prompts or multiple comparisons. Observed disparity alone does not establish discrimination or compliance.

Applicable divisions: ai-governance, cybersecurity

Research references:
- [NIST: Wilson proportion intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)

Example input:
```json
{
  "groups": [
    {
      "name": "Evaluation group A",
      "trials": 100,
      "failures": 3
    },
    {
      "name": "Evaluation group B",
      "trials": 40,
      "failures": 4
    }
  ],
  "failure_tolerance_percent": 10
}
```

### Stochastic debt fan scenarios

Engine `stochastic-debt` · version `1.0.0`

Seeded Monte Carlo debt paths with within-year correlated normal interest/growth shocks, independent across years. Report empirical 5/50/95 percentiles, terminal threshold frequency and worst-5% mean.

Limitations: Assumed distributions, not country calibration or an IMF DSA implementation. Interest draws are clipped to [-20,100]%, growth to [-95,200]%; clipping is counted. No default probability, exchange rates or fiscal feedback. Reproducibility depends on runtime as well as seed.

Applicable divisions: sovereign-debt, development-finance, climate-finance

Research references:
- [IMF: debt sustainability and uncertainty](https://www.imf.org/en/About/FAQ/mac-dsa)

Example input:
```json
{
  "initial_debt_percent_gdp": 90,
  "mean_interest_percent": 5,
  "mean_growth_percent": 4,
  "primary_surplus_percent_gdp": 1,
  "interest_std_pp": 1,
  "growth_std_pp": 2,
  "interest_growth_correlation": -0.3,
  "breach_threshold_percent_gdp": 100,
  "years": 10,
  "simulations": 500,
  "seed": 42
}
```

### Supply-network bottleneck optimization

Engine `supply-network` · version `1.0.0`

Edmonds–Karp residual-network maximum flow before and after edge disruptions; identify the disrupted minimum cut and verify max-flow/min-cut agreement.

Limitations: Single divisible commodity with one source and sink, common capacity units and one period. No transit time, cost, inventory, substitution, multicommodity competition or actual routing instruction.

Applicable divisions: critical-minerals, wto-trade, global-health, development-finance, ocean-governance

Research references:
- [NetworkX: maximum-flow and minimum-cut methods](https://networkx.org/documentation/stable/reference/algorithms/flow.html)

Example input:
```json
{
  "source": "Supply",
  "sink": "Demand",
  "required_throughput": 12,
  "edges": [
    {
      "origin": "Supply",
      "destination": "Port A",
      "capacity": 10,
      "disruption_percent": 50
    },
    {
      "origin": "Supply",
      "destination": "Port B",
      "capacity": 6,
      "disruption_percent": 0
    },
    {
      "origin": "Port A",
      "destination": "Demand",
      "capacity": 8,
      "disruption_percent": 0
    },
    {
      "origin": "Port B",
      "destination": "Demand",
      "capacity": 6,
      "disruption_percent": 0
    }
  ]
}
```

### Public-health SEIR scenario laboratory

Engine `health-seir` · version `1.0.0`

Compare baseline and contact-reduction SEIR paths using quarter-day exponential-hazard compartment transfers. Preserve population and nonnegative compartments; compare indicative capacity demand.

Limitations: Homogeneous synthetic population with constant assumed disease parameters. Demand is an infectious-stock proxy, not admissions or a clinical forecast. No age structure, births, deaths, waning, vaccination or calibration. Not for patient decisions.

Applicable divisions: global-health

Research references:
- [CDC: infectious-disease transmission models](https://www.cdc.gov/cfa-modeling-and-forecasting/about/explainer-transmission-models.html)

Example input:
```json
{
  "population": 100000,
  "initial_exposed": 50,
  "initial_infectious": 20,
  "reproduction_number": 2,
  "incubation_days": 5,
  "infectious_days": 7,
  "intervention_day": 20,
  "contact_reduction_percent": 40,
  "hospital_demand_fraction": 0.05,
  "hospital_capacity": 200,
  "days": 120
}
```

### Cross-domain impact propagation graph

Engine `cross-impact` · version `1.0.0`

Iterate x = direct shock + damping × transposed weighted influence matrix × x. Outgoing weight sums ≤1 and damping ≤0.95 make the iteration contractive; report indirect scenario scores.

Limitations: An assumed linear influence graph, not causal inference. Signed scores are dimensionless, not harm probabilities. Links need empirical justification and expert review; propagation is not proof of a real cross-sector effect.

Applicable divisions: nuclear-security, un-security-council, wto-trade, sovereign-debt, ai-governance, cybersecurity, global-health, space-security, critical-minerals, ocean-governance, international-tax, development-finance, climate-finance

Research references:
- [GGISP: explicitly defined contractive scenario model](/methods)

Example input:
```json
{
  "shocks": [
    {
      "division": "sovereign-debt",
      "initial_shock": 1
    }
  ],
  "links": [
    {
      "from_domain": "sovereign-debt",
      "to_domain": "development-finance",
      "transmission_weight": 0.7
    },
    {
      "from_domain": "development-finance",
      "to_domain": "global-health",
      "transmission_weight": 0.5
    },
    {
      "from_domain": "development-finance",
      "to_domain": "climate-finance",
      "transmission_weight": 0.5
    }
  ],
  "damping": 0.7
}
```

## Interpretation details

- Robust-policy outcomes must be comparable and higher-is-better. Negate consistently defined costs before using a lower-is-better quantity. Scenario outcomes are entered in the order of the scenario records. Pareto dominance and minimax regret do not require scenario probabilities; the weighted-mean comparison does use researcher-supplied relative weights. Zero-weight scenarios still participate in worst-case and regret calculations. Ties in maximin and weighted means list all matching option names. Minimax reports its tie count and breaks ties by higher worst outcome, then option name.
- Banzhaf enumeration counts all hypothetical coalitions symmetrically, respecting configured veto players. It does not estimate real coalition probabilities. Voting weights and quotas are entered in the same units.
- Wilson intervals are frequentist intervals under an independent binomial-trial assumption, not posterior credible intervals or guarantees of future AI performance. Per-group 95% coverage is not simultaneous coverage across all groups.
- Stochastic-debt draws are independent across years; within-year rate correlation uses two normal variates. Growth and interest are clipped to explicit bounds; the clipping count is returned. Tail statistics and threshold frequencies describe these assumed simulations only. A seeded run is repeatable in the same runtime; cross-runtime agreement is checked by the saved-run reproduction feature.
- The flow optimizer uses a residual network and verifies maximum-flow/minimum-cut agreement. Opposite-direction edges are allowed; duplicate directed edges are rejected. Returned flows are a mathematical capacity allocation, not operational dispatch. Residual capacities below 1e-10 are treated as numerical zero.
- SEIR uses simultaneous quarter-day exponential-hazard transfers S→E→I→R. It is a discrete approximation with preserved total population, not a calibrated epidemiological forecast. Capacity exceedance counts observation days 1 through the horizon, excluding day zero. Peaks are within the selected horizon and can occur at its boundary. Hospital demand is a fraction-of-infectious-stock proxy.
- The cross-domain graph solves x=s+d*A^T*x by iteration. Nonnegative outgoing link weights sum to at most one, and d≤0.95, making propagation contractive in the L1 norm. Direct shocks may be signed. Scores are dimensionless; links are assumed influences, not discovered causal effects. Iteration stops at a maximum coordinate change below 1e-10 or 500 iterations and reports convergence.

## Research grounding and limits

The [World Bank robust-decision work](https://ppp.worldbank.org/library/making-informed-investment-decisions-uncertain-world) motivates comparing strategies across uncertain futures. The [NIST proportion-interval reference](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) provides the statistical method used for benchmark intervals. [NetworkX flow documentation](https://networkx.org/documentation/stable/reference/algorithms/flow.html) identifies the maximum-flow and minimum-cut algorithm family; this project implements its own bounded Edmonds–Karp calculation without adding NetworkX as a dependency.

The [IMF description of sovereign risk analysis](https://www.imf.org/en/About/FAQ/mac-dsa) supports treating uncertainty explicitly; our simplified simulator does not reproduce the IMF framework. [CDC transmission-model guidance](https://www.cdc.gov/cfa-modeling-and-forecasting/about/explainer-transmission-models.html) explains compartmental modeling; it does not validate this implementation or its default assumptions.

For space risk, [NASA explains why proximity screening alone does not establish collision risk](https://www.nasa.gov/cara/step-2-close-approach-risk-assessment/). This release therefore adds decision-analysis methods for civilian policy research and does not present a disposal calculator as an orbital collision engine.

## Shared engineering integration

All twenty tools use validated schemas, browser forms, versioned study snapshots, exact source passages, data references, sensitivity routes where applicable, CSV export, human review and policy brief generation. Advanced methods are discoverable through the method-family filter and project-relevance filter. The local assistant suggests applicable cross-domain tools. No external AI, new package, autonomous institutional submission or remote execution is required.