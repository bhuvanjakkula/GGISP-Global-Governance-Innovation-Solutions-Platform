"""Bounded, deterministic research tools. Examples are synthetic, never country findings."""
from __future__ import annotations

import math
from typing import Annotated

from pydantic import Field, model_validator

from ggisp.modelling import DebtAssumptions, simulate

from ggisp.engine_types import Number, Percent, Fraction, Positive, Label, Inputs, unique, entry


class Control(Inputs):
    name: Label
    weight: Positive
    implementation_percent: Percent


class Safeguards(Inputs):
    controls: list[Control] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check(self):
        unique(self.controls)
        return self


def safeguards(a):
    total = sum(c.weight for c in a.controls)
    coverage = sum(c.weight * c.implementation_percent for c in a.controls) / total
    return {"metrics": {"weighted_coverage_percent": coverage, "remaining_gap_percent": 100-coverage},
            "rows": [{"control": c.name, "coverage_percent": c.implementation_percent,
                      "weighted_gap": c.weight * (1-c.implementation_percent/100)}
                     for c in sorted(a.controls, key=lambda c: c.weight*(100-c.implementation_percent), reverse=True)]}


class Member(Inputs):
    name: Label
    weight: Positive
    supports: bool
    veto: bool = False


class Voting(Inputs):
    members: list[Member] = Field(min_length=1, max_length=250)
    required_share_percent: Percent
    veto_enabled: bool

    @model_validator(mode="after")
    def check(self):
        unique(self.members)
        return self


def voting(a):
    share = sum(m.weight for m in a.members if m.supports)/sum(m.weight for m in a.members)*100
    blockers = [m.name for m in a.members if m.veto and not m.supports] if a.veto_enabled else []
    return {"metrics": {"support_share_percent": share, "passes": share >= a.required_share_percent and not blockers,
                        "veto_blockers": len(blockers)},
            "rows": [{"member": m.name, "supports": m.supports, "veto_blocks": m.name in blockers}
                     for m in a.members]}


class TradeItem(Inputs):
    name: Label
    import_value: Number
    baseline_tariff_percent: Percent
    policy_tariff_percent: Percent


class Trade(Inputs):
    items: list[TradeItem] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check(self):
        unique(self.items)
        return self


def trade(a):
    rows = [{"item": x.name, "baseline_duty": x.import_value*x.baseline_tariff_percent/100,
             "policy_duty": x.import_value*x.policy_tariff_percent/100} for x in a.items]
    baseline = sum(r["baseline_duty"] for r in rows)
    policy = sum(r["policy_duty"] for r in rows)
    return {"metrics": {"baseline_duty": baseline, "policy_duty": policy, "duty_change": policy-baseline}, "rows": rows}


class AIRisk(Inputs):
    name: Label
    likelihood: Fraction
    severity: Number
    mitigation_percent: Percent


class Assurance(Inputs):
    risks: list[AIRisk] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check(self):
        unique(self.risks)
        return self


def assurance(a):
    rows = [{"risk": r.name, "baseline_score": r.likelihood*r.severity,
             "residual_score": r.likelihood*r.severity*(1-r.mitigation_percent/100)} for r in a.risks]
    return {"metrics": {"baseline_score": sum(r["baseline_score"] for r in rows),
                        "residual_score": sum(r["residual_score"] for r in rows)},
            "rows": sorted(rows, key=lambda r: r["residual_score"], reverse=True)}


class CyberLoss(Inputs):
    annual_event_probability: Fraction
    impact_per_event: Number
    likelihood_reduction_percent: Percent
    impact_reduction_percent: Percent
    annual_control_cost: Number


def cyber(a):
    baseline = a.annual_event_probability * a.impact_per_event
    residual = baseline*(1-a.likelihood_reduction_percent/100)*(1-a.impact_reduction_percent/100)
    return {"metrics": {"baseline_expected_annual_loss": baseline, "residual_expected_annual_loss": residual,
                        "annual_control_cost": a.annual_control_cost,
                        "net_expected_annual_benefit": baseline-residual-a.annual_control_cost}, "rows": []}


class Region(Inputs):
    name: Label
    unmet_need: Number
    vulnerability_weight: Positive


class Allocation(Inputs):
    available_units: Number
    regions: list[Region] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check(self):
        unique(self.regions)
        return self


def allocation(a):
    # Capped weighted water filling: redistribute excess until no region exceeds its need.
    assigned = [0.0]*len(a.regions)
    remaining = min(a.available_units, sum(r.unmet_need for r in a.regions))
    active = {i for i,r in enumerate(a.regions) if r.unmet_need > 0}
    while active and remaining > 1e-9:
        weights = {i: a.regions[i].unmet_need*a.regions[i].vulnerability_weight for i in active}
        total = sum(weights.values())
        capped = {i for i in active if remaining*weights[i]/total >= a.regions[i].unmet_need-assigned[i]}
        if not capped:
            for i in active:
                assigned[i] += remaining*weights[i]/total
            remaining = 0
        else:
            for i in capped:
                amount = a.regions[i].unmet_need-assigned[i]
                assigned[i] += amount
                remaining -= amount
            active -= capped
    rows = [{"region":r.name, "allocated":assigned[i], "unmet_after":max(0,r.unmet_need-assigned[i])}
            for i,r in enumerate(a.regions)]
    used = sum(assigned)
    return {"metrics": {"allocated_units":used,"unused_units":max(0,a.available_units-used),
                        "remaining_unmet_need":sum(r["unmet_after"] for r in rows)}, "rows": rows}


class FleetGroup(Inputs):
    name: Label
    spacecraft_count: Annotated[int, Field(ge=0, le=1000000)]
    disposal_success_probability: Fraction


class Space(Inputs):
    groups: list[FleetGroup] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check(self):
        unique(self.groups)
        return self


def space(a):
    rows = [{"group":g.name,"expected_successful_disposals":g.spacecraft_count*g.disposal_success_probability,
             "expected_failed_disposals":g.spacecraft_count*(1-g.disposal_success_probability)} for g in a.groups]
    return {"metrics": {"spacecraft_count":sum(g.spacecraft_count for g in a.groups),
                        "expected_failed_disposals":sum(r["expected_failed_disposals"] for r in rows)}, "rows":rows}


class Supplier(Inputs):
    name: Label
    share_percent: Percent
    disrupted: bool = False


class Minerals(Inputs):
    suppliers: list[Supplier] = Field(min_length=1,max_length=100)
    replacement_capacity_percent: Percent

    @model_validator(mode="after")
    def check(self):
        unique(self.suppliers)
        if not math.isclose(sum(s.share_percent for s in self.suppliers),100,abs_tol=1e-6):
            raise ValueError("Supplier shares must total 100 percent")
        return self


def minerals(a):
    disrupted = sum(s.share_percent for s in a.suppliers if s.disrupted)
    return {"metrics": {"concentration_hhi":sum(s.share_percent**2 for s in a.suppliers),
                        "disrupted_share_percent":disrupted,
                        "uncovered_shortfall_percent":max(0,disrupted-a.replacement_capacity_percent)},
            "rows":[{"supplier":s.name,"share_percent":s.share_percent,"disrupted":s.disrupted} for s in a.suppliers]}


class Ocean(Inputs):
    initial_pollution_tonnes: Number
    annual_inflow_tonnes: Number
    prevention_percent: Percent
    annual_cleanup_capacity_tonnes: Number
    years: Annotated[int, Field(ge=1,le=50)]


def ocean(a):
    stock = a.initial_pollution_tonnes
    rows = [{"year":0,"pollution_tonnes":stock,"removed_tonnes":0.0}]
    for year in range(1,a.years+1):
        stock += a.annual_inflow_tonnes*(1-a.prevention_percent/100)
        removed = min(stock,a.annual_cleanup_capacity_tonnes)
        stock -= removed
        rows.append({"year":year,"pollution_tonnes":stock,"removed_tonnes":removed})
    return {"metrics":{"terminal_pollution_tonnes":stock,"removed_tonnes":sum(r["removed_tonnes"] for r in rows)},"rows":rows}


class Tax(Inputs):
    taxable_base: Number
    baseline_effective_rate_percent: Percent
    policy_effective_rate_percent: Percent
    policy_base_change_percent: Annotated[float, Field(ge=-100,le=1000,allow_inf_nan=False)]
    annual_administration_cost: Number


def tax(a):
    baseline = a.taxable_base*a.baseline_effective_rate_percent/100
    policy = a.taxable_base*(1+a.policy_base_change_percent/100)*a.policy_effective_rate_percent/100
    return {"metrics":{"baseline_revenue":baseline,"policy_gross_revenue":policy,
                       "policy_net_revenue":policy-a.annual_administration_cost,
                       "net_revenue_change":policy-a.annual_administration_cost-baseline},"rows":[]}


class Investment(Inputs):
    name: Label
    division: Label
    cost: Positive
    benefit_score: Number
    delivery_probability: Fraction
    equity_multiplier: Annotated[float, Field(ge=0,le=10,allow_inf_nan=False)]
    requires: list[Label] = Field(default_factory=list,max_length=16)


class Synergy(Inputs):
    first: Label
    second: Label
    benefit_score: Annotated[float, Field(ge=-1e12,le=1e12,allow_inf_nan=False)]


class Portfolio(Inputs):
    budget: Number
    investments: list[Investment] = Field(min_length=1,max_length=16)
    synergies: list[Synergy] = Field(default_factory=list,max_length=120)

    @model_validator(mode="after")
    def check(self):
        from ggisp.db import DOMAINS
        unique(self.investments)
        names = {x.name for x in self.investments}
        allowed = {x[0] for x in DOMAINS}
        for x in self.investments:
            if x.division not in allowed:
                raise ValueError("Investment division must be a GGISP domain slug")
            if len(x.requires) != len(set(x.requires)) or x.name in x.requires or not set(x.requires)<=names:
                raise ValueError("Dependencies must be unique other investment names")
        pairs=set()
        for s in self.synergies:
            pair=tuple(sorted([s.first,s.second]))
            if s.first==s.second or not {s.first,s.second}<=names or pair in pairs:
                raise ValueError("Synergies require a unique pair of different known investments")
            pairs.add(pair)
        # Reject circular dependencies instead of silently treating them as bundles.
        graph={x.name:x.requires for x in self.investments}
        def visit(name,trail):
            if name in trail: raise ValueError("Dependency cycle detected")
            for dependency in graph[name]: visit(dependency,trail|{name})
        for name in names: visit(name,set())
        return self


def portfolio(a):
    n=len(a.investments)
    best_score=0.0; best_cost=0.0; best_names=set(); feasible=0
    for mask in range(1<<n):
        chosen=[a.investments[i] for i in range(n) if mask & (1<<i)]
        cost=sum(x.cost for x in chosen)
        if cost>a.budget: continue
        names={x.name for x in chosen}
        if any(not set(x.requires)<=names for x in chosen): continue
        feasible+=1
        score=sum(x.benefit_score*x.delivery_probability*x.equity_multiplier for x in chosen)
        score+=sum(s.benefit_score for s in a.synergies if {s.first,s.second}<=names)
        if score>best_score or (score==best_score and cost<best_cost):
            best_score,best_cost,best_names=score,cost,names
    return {"metrics":{"selected_score":best_score,"spent":best_cost,"unspent":a.budget-best_cost,
                        "selected_count":len(best_names),"feasible_subsets_evaluated":feasible},
            "rows":[{"investment":x.name,"division":x.division,"selected":x.name in best_names,
                     "cost":x.cost,"adjusted_benefit":x.benefit_score*x.delivery_probability*x.equity_multiplier}
                    for x in a.investments]}


class Climate(Inputs):
    baseline_annual_emissions_tonnes: Number
    reduction_percent: Percent
    annual_program_cost: Number
    committed_funding: Number
    years: Annotated[int, Field(ge=1,le=50)]


def climate(a):
    avoided=a.baseline_annual_emissions_tonnes*a.reduction_percent/100*a.years
    cost=a.annual_program_cost*a.years
    return {"metrics":{"cumulative_avoided_tonnes":avoided,"total_program_cost":cost,
                        "funding_gap":max(0,cost-a.committed_funding),
                        "cost_per_avoided_tonne":cost/avoided if avoided else None},
            "rows":[{"year":y,"baseline_tonnes":a.baseline_annual_emissions_tonnes,
                     "policy_tonnes":a.baseline_annual_emissions_tonnes*(1-a.reduction_percent/100)}
                    for y in range(1,a.years+1)]}


def debt(a):
    result=simulate(a)
    return {"metrics":{"terminal_debt_percent_gdp":result['values'][-1]['debt_percent_gdp'],
                        "change_percentage_points":result['values'][-1]['debt_percent_gdp']-a.initial_debt_percent_gdp},
            "rows":result['values']}


ENGINES = {
    "safeguards":entry("nuclear-security","Peaceful safeguards review",Safeguards,safeguards,
        {"controls":[{"name":"Review of public safeguards reporting","weight":3,"implementation_percent":50},
                     {"name":"Independent policy review","weight":2,"implementation_percent":20}]},
        "Weighted mean of researcher-assigned implementation percentages; gaps ranked by weight × uncovered share.",
        "Checklist completeness only. Does not estimate nuclear risk, inspect facilities or establish treaty compliance."),
    "voting":entry("un-security-council","Institutional voting design",Voting,voting,
        {"members":[{"name":"Group A","weight":3,"supports":True,"veto":True},
                    {"name":"Group B","weight":2,"supports":False,"veto":True},
                    {"name":"Group C","weight":5,"supports":True,"veto":False}],
         "required_share_percent":60,"veto_enabled":True},
        "Support weight / total weight; a proposal passes when its configured threshold is met and no enabled veto blocks it.",
        "A hypothetical institutional design, not an implementation of current UN rules or a diplomatic feasibility forecast."),
    "trade":entry("wto-trade","Tariff basket comparison",Trade,trade,
        {"items":[{"name":"Illustrative machinery","import_value":1000000,"baseline_tariff_percent":10,"policy_tariff_percent":6},
                  {"name":"Illustrative materials","import_value":500000,"baseline_tariff_percent":5,"policy_tariff_percent":3}]},
        "Sum import value × tariff rate for a fixed basket before and after the policy.",
        "Use one currency and period. Omits demand, exchange rates, exemptions, retaliation and legal compatibility."),
    "debt":entry("sovereign-debt","Debt trajectory",DebtAssumptions,debt,
        {"initial_debt_percent_gdp":90,"interest_rate_percent":5,"nominal_gdp_growth_percent":4,"primary_surplus_percent_gdp":1,"years":10},
        "d[t+1] = d[t] × (1+i)/(1+g) − primary surplus. Rates are nominal.",
        "Constant-assumption illustration, not a country forecast. Negative values mean net assets in this equation."),
    "ai-assurance":entry("ai-governance","AI assurance risk register",Assurance,assurance,
        {"risks":[{"name":"Unsupported citations","likelihood":0.5,"severity":8,"mitigation_percent":40},
                  {"name":"Unequal performance","likelihood":0.3,"severity":9,"mitigation_percent":20}]},
        "Baseline score = likelihood × severity. Residual score = baseline × (1−mitigation share).",
        "Subjective prioritization rubric. Scores are not calibrated probabilities of harm, certification or regulatory compliance."),
    "cyber-loss":entry("cybersecurity","Defensive investment economics",CyberLoss,cyber,
        {"annual_event_probability":0.2,"impact_per_event":1000000,"likelihood_reduction_percent":40,
         "impact_reduction_percent":25,"annual_control_cost":30000},
        "Expected annual loss = event probability × impact. Apply assumed likelihood and impact reductions multiplicatively.",
        "A single-event annual scenario, using one currency. Effectiveness is assumed; correlated events and adversary adaptation are omitted."),
    "health-allocation":entry("global-health","Equitable resource allocation",Allocation,allocation,
        {"available_units":1000,"regions":[{"name":"Region A","unmet_need":800,"vulnerability_weight":2},
                                             {"name":"Region B","unmet_need":600,"vulnerability_weight":1}]},
        "Allocate proportional to unmet need × vulnerability, cap at regional need, then redistribute excess.",
        "Divisible public resource planning only; no patient decisions. Need and equity weights require review; logistics are omitted."),
    "space-disposal":entry("space-security","Civilian fleet disposal planning",Space,space,
        {"groups":[{"name":"Fleet A","spacecraft_count":100,"disposal_success_probability":0.9},
                   {"name":"Fleet B","spacecraft_count":50,"disposal_success_probability":0.8}]},
        "Expected failed disposals = fleet count × (1−assumed disposal success probability).",
        "Portfolio expectation only. No orbit propagation, collision prediction, maneuver advice or regulatory compliance assessment."),
    "minerals":entry("critical-minerals","Supply concentration and disruption",Minerals,minerals,
        {"suppliers":[{"name":"Supplier A","share_percent":60,"disrupted":True},
                      {"name":"Supplier B","share_percent":40,"disrupted":False}],"replacement_capacity_percent":20},
        "HHI = sum of squared percentage shares. Shortfall = max(0, disrupted share − additional replacement capacity).",
        "Replacement capacity must be additional to the listed supply. Omits inventory, substitution, prices and recovery time."),
    "ocean":entry("ocean-governance","Pollution prevention and cleanup",Ocean,ocean,
        {"initial_pollution_tonnes":1000,"annual_inflow_tonnes":200,"prevention_percent":40,"annual_cleanup_capacity_tonnes":150,"years":10},
        "Each year add unprevented inflow, then remove up to cleanup capacity without allowing negative stock.",
        "Closed-box material accounting only; excludes transport, degradation, ecosystems and measurement uncertainty."),
    "tax":entry("international-tax","Fiscal revenue scenario",Tax,tax,
        {"taxable_base":10000000,"baseline_effective_rate_percent":15,"policy_effective_rate_percent":18,
         "policy_base_change_percent":-5,"annual_administration_cost":100000},
        "Revenue = taxable base × effective rate. Apply assumed base change and subtract administration cost for policy net revenue.",
        "Use one currency and fiscal period. Not tax advice, legal interpretation or a model of actual corporate responses."),
    "portfolio":entry("development-finance","Cross-domain investment optimizer",Portfolio,portfolio,
        {"budget":100,"investments":[
            {"name":"Evidence infrastructure","division":"ai-governance","cost":30,"benefit_score":35,"delivery_probability":0.9,"equity_multiplier":1,"requires":[]},
            {"name":"Water resilience","division":"climate-finance","cost":60,"benefit_score":80,"delivery_probability":0.8,"equity_multiplier":1.2,"requires":["Evidence infrastructure"]},
            {"name":"Health supplies","division":"global-health","cost":50,"benefit_score":65,"delivery_probability":0.9,"equity_multiplier":1.1,"requires":[]}],
         "synergies":[{"first":"Evidence infrastructure","second":"Water resilience","benefit_score":10}]},
        "Exhaustive search over at most 16 investments. Maximize comparable benefit × delivery probability × equity, plus user-assigned pair synergies, subject to budget and dependencies. Tie-break on lower cost.",
        "An exact optimum only for the entered scoring model. Scores and synergies must share units. No causal benefit estimation, market return or automatic spending."),
    "climate":entry("climate-finance","Climate funding and abatement",Climate,climate,
        {"baseline_annual_emissions_tonnes":100000,"reduction_percent":20,"annual_program_cost":1000000,"committed_funding":3000000,"years":5},
        "Avoided tonnes = annual baseline × reduction share × years. Funding gap = max(0, program cost − committed funding).",
        "Flat emissions baseline; no discounting, leakage, additionality, rebound or lifecycle validation. Funding and cost must use one currency."),
}


def calculate_engine(engine_id, parameters):
    engine=ENGINES[engine_id]
    validated=engine['schema'].model_validate(parameters)
    output=engine['calculate'](validated)
    return validated.model_dump(), {"engine_id":engine_id,"model_version":engine['version'],
            "method":engine['method'],"limitations":engine['limitations'],
            "input_status":"User-supplied assumptions; not independently verified",**output}


from ggisp.advanced import ADVANCED_ENGINES
ENGINES.update(ADVANCED_ENGINES)
