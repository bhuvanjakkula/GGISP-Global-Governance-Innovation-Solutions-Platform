# Analytical methods and scope — v0.4

All defaults in the tool catalog are fictional. These implementations are transparent research calculations, not independently validated specialist forecasting systems. Input units and limitations are part of each tool.

## Peaceful safeguards review

Division: `nuclear-security` · engine: `safeguards` · version: `1.0.0`

Weighted mean of researcher-assigned implementation percentages; gaps ranked by weight × uncovered share.

Limits: Checklist completeness only. Does not estimate nuclear risk, inspect facilities or establish treaty compliance.

Example input:
```json
{
  "controls": [
    {
      "name": "Review of public safeguards reporting",
      "weight": 3,
      "implementation_percent": 50
    },
    {
      "name": "Independent policy review",
      "weight": 2,
      "implementation_percent": 20
    }
  ]
}
```

## Institutional voting design

Division: `un-security-council` · engine: `voting` · version: `1.0.0`

Support weight / total weight; a proposal passes when its configured threshold is met and no enabled veto blocks it.

Limits: A hypothetical institutional design, not an implementation of current UN rules or a diplomatic feasibility forecast.

Example input:
```json
{
  "members": [
    {
      "name": "Group A",
      "weight": 3,
      "supports": true,
      "veto": true
    },
    {
      "name": "Group B",
      "weight": 2,
      "supports": false,
      "veto": true
    },
    {
      "name": "Group C",
      "weight": 5,
      "supports": true,
      "veto": false
    }
  ],
  "required_share_percent": 60,
  "veto_enabled": true
}
```

## Tariff basket comparison

Division: `wto-trade` · engine: `trade` · version: `1.0.0`

Sum import value × tariff rate for a fixed basket before and after the policy.

Limits: Use one currency and period. Omits demand, exchange rates, exemptions, retaliation and legal compatibility.

Example input:
```json
{
  "items": [
    {
      "name": "Illustrative machinery",
      "import_value": 1000000,
      "baseline_tariff_percent": 10,
      "policy_tariff_percent": 6
    },
    {
      "name": "Illustrative materials",
      "import_value": 500000,
      "baseline_tariff_percent": 5,
      "policy_tariff_percent": 3
    }
  ]
}
```

## Debt trajectory

Division: `sovereign-debt` · engine: `debt` · version: `1.0.0`

d[t+1] = d[t] × (1+i)/(1+g) − primary surplus. Rates are nominal.

Limits: Constant-assumption illustration, not a country forecast. Negative values mean net assets in this equation.

Example input:
```json
{
  "initial_debt_percent_gdp": 90,
  "interest_rate_percent": 5,
  "nominal_gdp_growth_percent": 4,
  "primary_surplus_percent_gdp": 1,
  "years": 10
}
```

## AI assurance risk register

Division: `ai-governance` · engine: `ai-assurance` · version: `1.0.0`

Baseline score = likelihood × severity. Residual score = baseline × (1−mitigation share).

Limits: Subjective prioritization rubric. Scores are not calibrated probabilities of harm, certification or regulatory compliance.

Example input:
```json
{
  "risks": [
    {
      "name": "Unsupported citations",
      "likelihood": 0.5,
      "severity": 8,
      "mitigation_percent": 40
    },
    {
      "name": "Unequal performance",
      "likelihood": 0.3,
      "severity": 9,
      "mitigation_percent": 20
    }
  ]
}
```

## Defensive investment economics

Division: `cybersecurity` · engine: `cyber-loss` · version: `1.0.0`

Expected annual loss = event probability × impact. Apply assumed likelihood and impact reductions multiplicatively.

Limits: A single-event annual scenario, using one currency. Effectiveness is assumed; correlated events and adversary adaptation are omitted.

Example input:
```json
{
  "annual_event_probability": 0.2,
  "impact_per_event": 1000000,
  "likelihood_reduction_percent": 40,
  "impact_reduction_percent": 25,
  "annual_control_cost": 30000
}
```

## Equitable resource allocation

Division: `global-health` · engine: `health-allocation` · version: `1.0.0`

Allocate proportional to unmet need × vulnerability, cap at regional need, then redistribute excess.

Limits: Divisible public resource planning only; no patient decisions. Need and equity weights require review; logistics are omitted.

Example input:
```json
{
  "available_units": 1000,
  "regions": [
    {
      "name": "Region A",
      "unmet_need": 800,
      "vulnerability_weight": 2
    },
    {
      "name": "Region B",
      "unmet_need": 600,
      "vulnerability_weight": 1
    }
  ]
}
```

## Civilian fleet disposal planning

Division: `space-security` · engine: `space-disposal` · version: `1.0.0`

Expected failed disposals = fleet count × (1−assumed disposal success probability).

Limits: Portfolio expectation only. No orbit propagation, collision prediction, maneuver advice or regulatory compliance assessment.

Example input:
```json
{
  "groups": [
    {
      "name": "Fleet A",
      "spacecraft_count": 100,
      "disposal_success_probability": 0.9
    },
    {
      "name": "Fleet B",
      "spacecraft_count": 50,
      "disposal_success_probability": 0.8
    }
  ]
}
```

## Supply concentration and disruption

Division: `critical-minerals` · engine: `minerals` · version: `1.0.0`

HHI = sum of squared percentage shares. Shortfall = max(0, disrupted share − additional replacement capacity).

Limits: Replacement capacity must be additional to the listed supply. Omits inventory, substitution, prices and recovery time.

Example input:
```json
{
  "suppliers": [
    {
      "name": "Supplier A",
      "share_percent": 60,
      "disrupted": true
    },
    {
      "name": "Supplier B",
      "share_percent": 40,
      "disrupted": false
    }
  ],
  "replacement_capacity_percent": 20
}
```

## Pollution prevention and cleanup

Division: `ocean-governance` · engine: `ocean` · version: `1.0.0`

Each year add unprevented inflow, then remove up to cleanup capacity without allowing negative stock.

Limits: Closed-box material accounting only; excludes transport, degradation, ecosystems and measurement uncertainty.

Example input:
```json
{
  "initial_pollution_tonnes": 1000,
  "annual_inflow_tonnes": 200,
  "prevention_percent": 40,
  "annual_cleanup_capacity_tonnes": 150,
  "years": 10
}
```

## Fiscal revenue scenario

Division: `international-tax` · engine: `tax` · version: `1.0.0`

Revenue = taxable base × effective rate. Apply assumed base change and subtract administration cost for policy net revenue.

Limits: Use one currency and fiscal period. Not tax advice, legal interpretation or a model of actual corporate responses.

Example input:
```json
{
  "taxable_base": 10000000,
  "baseline_effective_rate_percent": 15,
  "policy_effective_rate_percent": 18,
  "policy_base_change_percent": -5,
  "annual_administration_cost": 100000
}
```

## Cross-domain investment optimizer

Division: `development-finance` · engine: `portfolio` · version: `1.0.0`

Exhaustive search over at most 16 investments. Maximize comparable benefit × delivery probability × equity, plus user-assigned pair synergies, subject to budget and dependencies. Tie-break on lower cost.

Limits: An exact optimum only for the entered scoring model. Scores and synergies must share units. No causal benefit estimation, market return or automatic spending.

Example input:
```json
{
  "budget": 100,
  "investments": [
    {
      "name": "Evidence infrastructure",
      "division": "ai-governance",
      "cost": 30,
      "benefit_score": 35,
      "delivery_probability": 0.9,
      "equity_multiplier": 1,
      "requires": []
    },
    {
      "name": "Water resilience",
      "division": "climate-finance",
      "cost": 60,
      "benefit_score": 80,
      "delivery_probability": 0.8,
      "equity_multiplier": 1.2,
      "requires": [
        "Evidence infrastructure"
      ]
    },
    {
      "name": "Health supplies",
      "division": "global-health",
      "cost": 50,
      "benefit_score": 65,
      "delivery_probability": 0.9,
      "equity_multiplier": 1.1,
      "requires": []
    }
  ],
  "synergies": [
    {
      "first": "Evidence infrastructure",
      "second": "Water resilience",
      "benefit_score": 10
    }
  ]
}
```

## Climate funding and abatement

Division: `climate-finance` · engine: `climate` · version: `1.0.0`

Avoided tonnes = annual baseline × reduction share × years. Funding gap = max(0, program cost − committed funding).

Limits: Flat emissions baseline; no discounting, leakage, additionality, rebound or lifecycle validation. Funding and cost must use one currency.

Example input:
```json
{
  "baseline_annual_emissions_tonnes": 100000,
  "reduction_percent": 20,
  "annual_program_cost": 1000000,
  "committed_funding": 3000000,
  "years": 5
}
```

## Method references

The supply concentration calculation uses the sum-of-squared-percentage-shares definition described by the [US Department of Justice](https://www.justice.gov/atr/herfindahl-hirschman-index). This app does not apply merger-law thresholds or make antitrust conclusions.

The on-demand data importer follows the World Bank [API structure](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures) and [indicator query documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries). Each import stores its exact requested URL, raw decoded API response, retrieval time, normalized observations, skipped-null count and provider lastupdated field.

All other tools are explicitly specified arithmetic or researcher-defined rubrics. They do not claim a new scientific discovery or institutional standard.