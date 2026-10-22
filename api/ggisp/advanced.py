"""Advanced scenario methods; transparent implementations, not calibrated predictions."""
from collections import deque
import math
import random
from typing import Annotated

from pydantic import Field, model_validator

from ggisp.db import DOMAINS
from ggisp.engine_types import Inputs, Number, Percent, Positive, Fraction, Label, unique, entry

ALL_DOMAINS=[d[0] for d in DOMAINS]
Score=Annotated[float,Field(ge=-1e12,le=1e12,allow_inf_nan=False)]


class Scenario(Inputs):
    name: Label
    weight: Number


class PolicyOption(Inputs):
    name: Label
    outcomes: list[Score]=Field(min_length=1,max_length=30)


class RobustChoice(Inputs):
    scenarios: list[Scenario]=Field(min_length=1,max_length=30)
    options: list[PolicyOption]=Field(min_length=2,max_length=50)

    @model_validator(mode='after')
    def check(self):
        unique(self.scenarios);unique(self.options)
        if sum(s.weight for s in self.scenarios)<=0:raise ValueError('At least one scenario weight must be positive')
        if any(len(o.outcomes)!=len(self.scenarios) for o in self.options):
            raise ValueError('Each option needs one outcome per scenario, in scenario order')
        return self


def robust(a):
    best=[max(o.outcomes[i] for o in a.options) for i in range(len(a.scenarios))]
    total=sum(s.weight for s in a.scenarios)
    rows=[]
    for o in a.options:
        dominated=any(all(x>=y for x,y in zip(other.outcomes,o.outcomes)) and
                      any(x>y for x,y in zip(other.outcomes,o.outcomes)) for other in a.options)
        rows.append({'option':o.name,'weighted_mean':sum(v*s.weight for v,s in zip(o.outcomes,a.scenarios))/total,
                     'worst_outcome':min(o.outcomes),'maximum_regret':max(b-v for b,v in zip(best,o.outcomes)),
                     'pareto_dominated':dominated})
    by_regret=sorted(rows,key=lambda r:(r['maximum_regret'],-r['worst_outcome'],r['option']))
    maximin=max(r['worst_outcome'] for r in rows)
    best_mean=max(r['weighted_mean'] for r in rows)
    return {'metrics':{'minimax_regret_choice':by_regret[0]['option'],
                       'minimax_regret':by_regret[0]['maximum_regret'],
                       'minimax_regret_tied_options':sum(r['maximum_regret']==by_regret[0]['maximum_regret'] for r in rows),
                       'maximin_choice':'; '.join(r['option'] for r in rows if r['worst_outcome']==maximin),
                       'weighted_mean_choice':'; '.join(r['option'] for r in rows if r['weighted_mean']==best_mean),
                       'pareto_efficient_options':sum(not r['pareto_dominated'] for r in rows)},'rows':by_regret}


class VotingPlayer(Inputs):
    name: Label
    weight: Positive
    veto: bool=False


class VotingPower(Inputs):
    players: list[VotingPlayer]=Field(min_length=1,max_length=16)
    quota: Positive

    @model_validator(mode='after')
    def check(self):
        unique(self.players)
        if self.quota>sum(p.weight for p in self.players):raise ValueError('Quota exceeds total voting weight')
        return self


def voting_power(a):
    n=len(a.players);swings=[0]*n;winning=0
    veto_mask=sum(1<<i for i,p in enumerate(a.players) if p.veto)
    weights=[0.0]*(1<<n)
    for mask in range(1,1<<n):
        bit=mask & -mask;i=bit.bit_length()-1
        weights[mask]=weights[mask^bit]+a.players[i].weight
    def wins(mask):return weights[mask]>=a.quota and mask & veto_mask==veto_mask
    for mask in range(1<<n):
        if wins(mask):winning+=1;continue
        for i in range(n):
            if not mask & (1<<i) and wins(mask | (1<<i)):swings[i]+=1
    total=sum(swings)
    return {'metrics':{'coalitions_evaluated':1<<n,'winning_coalitions':winning,'total_critical_swings':total},
            'rows':[{'player':p.name,'voting_weight':p.weight,'critical_swings':swings[i],
                     'normalized_banzhaf_power':swings[i]/total if total else 0,
                     'absolute_banzhaf_power':swings[i]/(1<<(n-1))} for i,p in enumerate(a.players)]}


class EvaluationGroup(Inputs):
    name: Label
    trials: Annotated[int,Field(ge=1,le=1000000000)]
    failures: Annotated[int,Field(ge=0,le=1000000000)]

    @model_validator(mode='after')
    def check(self):
        if self.failures>self.trials:raise ValueError('Failures cannot exceed trials')
        return self


class BenchmarkAudit(Inputs):
    groups: list[EvaluationGroup]=Field(min_length=1,max_length=100)
    failure_tolerance_percent: Percent

    @model_validator(mode='after')
    def check(self):unique(self.groups);return self


def wilson(failures,n):
    z=1.959963984540054;p=failures/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0,center-half),min(1,center+half)


def benchmark(a):
    rows=[]
    for g in a.groups:
        lower,upper=wilson(g.failures,g.trials)
        rows.append({'group':g.name,'trials':g.trials,'failures':g.failures,'failure_rate_percent':100*g.failures/g.trials,
                     'wilson_95_lower_percent':100*lower,'wilson_95_upper_percent':100*upper,
                     'upper_bound_within_tolerance':100*upper<=a.failure_tolerance_percent})
    total=sum(g.trials for g in a.groups);failures=sum(g.failures for g in a.groups)
    return {'metrics':{'total_trials':total,'pooled_failure_rate_percent':100*failures/total,
                       'observed_group_gap_pp':max(r['failure_rate_percent'] for r in rows)-min(r['failure_rate_percent'] for r in rows),
                       'groups_with_upper_bound_above_tolerance':sum(not r['upper_bound_within_tolerance'] for r in rows)},'rows':rows}


class StochasticDebt(Inputs):
    initial_debt_percent_gdp: Annotated[float,Field(ge=0,le=1000)]
    mean_interest_percent: Annotated[float,Field(ge=-20,le=100)]
    mean_growth_percent: Annotated[float,Field(ge=-95,le=200)]
    primary_surplus_percent_gdp: Annotated[float,Field(ge=-40,le=40)]
    interest_std_pp: Annotated[float,Field(ge=0,le=30)]
    growth_std_pp: Annotated[float,Field(ge=0,le=30)]
    interest_growth_correlation: Annotated[float,Field(ge=-1,le=1)]
    breach_threshold_percent_gdp: Number
    years: Annotated[int,Field(ge=1,le=30)]
    simulations: Annotated[int,Field(ge=20,le=5000)]
    seed: Annotated[int,Field(ge=0,le=2147483647)]


def quantile(values,p):
    ordered=sorted(values);position=(len(ordered)-1)*p;left=int(position);right=min(left+1,len(ordered)-1)
    return ordered[left]+(ordered[right]-ordered[left])*(position-left)


def stochastic_debt(a):
    rng=random.Random(a.seed);paths=[[a.initial_debt_percent_gdp] for _ in range(a.simulations)]
    clipped=0;rho=a.interest_growth_correlation;rho_scale=math.sqrt(max(0,1-rho*rho))
    for path in paths:
        for _ in range(a.years):
            z1=rng.gauss(0,1);z2=rng.gauss(0,1)
            raw_i=a.mean_interest_percent+a.interest_std_pp*z1
            raw_g=a.mean_growth_percent+a.growth_std_pp*(rho*z1+rho_scale*z2)
            i=min(100,max(-20,raw_i));g=min(200,max(-95,raw_g))
            clipped+=int(i!=raw_i)+int(g!=raw_g)
            debt=path[-1]*(1+i/100)/(1+g/100)-a.primary_surplus_percent_gdp
            if abs(debt)>1e12:raise ValueError('A simulated trajectory exceeds the numerical range; reduce stress assumptions')
            path.append(debt)
    terminal=[p[-1] for p in paths];rows=[]
    for year in range(a.years+1):
        values=[p[year] for p in paths]
        rows.append({'year':year,'p05_debt_percent_gdp':quantile(values,.05),
                     'median_debt_percent_gdp':quantile(values,.5),'p95_debt_percent_gdp':quantile(values,.95)})
    tail=sorted(terminal,reverse=True)[:max(1,math.ceil(.05*a.simulations))]
    return {'metrics':{'terminal_median_debt_percent_gdp':quantile(terminal,.5),
                       'terminal_threshold_exceedance_fraction':sum(v>a.breach_threshold_percent_gdp for v in terminal)/a.simulations,
                       'mean_of_worst_five_percent':sum(tail)/len(tail),
                       'clipped_rate_draws':clipped,'seed':a.seed,'simulations':a.simulations},'rows':rows}


class FlowEdge(Inputs):
    origin: Label
    destination: Label
    capacity: Number
    disruption_percent: Percent


class SupplyNetwork(Inputs):
    source: Label
    sink: Label
    required_throughput: Number
    edges: list[FlowEdge]=Field(min_length=1,max_length=150)

    @model_validator(mode='after')
    def check(self):
        pairs=[(e.origin,e.destination) for e in self.edges]
        nodes={v for p in pairs for v in p}
        if len(nodes)>40 or len(set(pairs))!=len(pairs) or any(u==v for u,v in pairs):
            raise ValueError('Use at most 40 nodes, unique directed edges and no self loops')
        if self.source==self.sink or self.source not in nodes or self.sink not in nodes:
            raise ValueError('Choose different source and sink nodes present in the edges')
        return self


def maxflow(a,disrupted):
    nodes=sorted({n for e in a.edges for n in (e.origin,e.destination)})
    capacity={u:{v:0.0 for v in nodes} for u in nodes}
    for e in a.edges:capacity[e.origin][e.destination]=e.capacity*(1-e.disruption_percent/100) if disrupted else e.capacity
    residual={u:dict(v) for u,v in capacity.items()};total=0.0
    while True:
        parent={a.source:None};queue=deque([a.source])
        while queue and a.sink not in parent:
            u=queue.popleft()
            for v in nodes:
                if v not in parent and residual[u][v]>1e-10:parent[v]=u;queue.append(v)
        if a.sink not in parent:break
        flow=float('inf');v=a.sink
        while parent[v] is not None:flow=min(flow,residual[parent[v]][v]);v=parent[v]
        v=a.sink
        while parent[v] is not None:
            u=parent[v];residual[u][v]-=flow;residual[v][u]+=flow;v=u
        total+=flow
    reachable=set(parent)
    cut=sum(capacity[u][v] for u in reachable for v in nodes if v not in reachable)
    flows={(e.origin,e.destination):max(0,capacity[e.origin][e.destination]-residual[e.origin][e.destination]) for e in a.edges}
    return total,cut,reachable,flows


def supply_network(a):
    baseline,_,_,baseflows=maxflow(a,False);actual,cut,reachable,flows=maxflow(a,True)
    return {'metrics':{'baseline_maximum_throughput':baseline,'disrupted_maximum_throughput':actual,
                       'unmet_required_throughput':max(0,a.required_throughput-actual),
                       'disrupted_minimum_cut_capacity':cut,'max_flow_min_cut_gap':abs(actual-cut)},
            'rows':[{'origin':e.origin,'destination':e.destination,'baseline_flow':baseflows[(e.origin,e.destination)],
                     'disrupted_flow':flows[(e.origin,e.destination)],
                     'disrupted_capacity':e.capacity*(1-e.disruption_percent/100),
                     'in_disrupted_minimum_cut':e.origin in reachable and e.destination not in reachable} for e in a.edges]}


class SEIR(Inputs):
    population: Annotated[float,Field(ge=1,le=1e9)]
    initial_exposed: Number
    initial_infectious: Number
    reproduction_number: Annotated[float,Field(ge=0,le=20)]
    incubation_days: Annotated[float,Field(ge=1,le=100)]
    infectious_days: Annotated[float,Field(ge=1,le=100)]
    intervention_day: Annotated[int,Field(ge=0,le=365)]
    contact_reduction_percent: Percent
    hospital_demand_fraction: Fraction
    hospital_capacity: Number
    days: Annotated[int,Field(ge=1,le=365)]

    @model_validator(mode='after')
    def check(self):
        if self.initial_exposed+self.initial_infectious>self.population:
            raise ValueError('Initial exposed and infectious groups cannot exceed population')
        if self.intervention_day>self.days:raise ValueError('Intervention day must fall within the study horizon')
        return self


def seir_path(a,reduction):
    s=a.population-a.initial_exposed-a.initial_infectious;e=a.initial_exposed;i=a.initial_infectious;r=0.0
    rows=[(s,e,i,r)]
    for day in range(a.days):
        beta=a.reproduction_number/a.infectious_days*(1-reduction/100 if day>=a.intervention_day else 1)
        for _ in range(4):
            exposed=s*(-math.expm1(-beta*i/a.population*.25))
            infectious=e*(-math.expm1(-.25/a.incubation_days))
            recovered=i*(-math.expm1(-.25/a.infectious_days))
            s-=exposed;e+=exposed-infectious;i+=infectious-recovered;r+=recovered
        rows.append((s,e,i,r))
    return rows


def seir(a):
    base=seir_path(a,0);policy=seir_path(a,a.contact_reduction_percent)
    peak_base=max(v[2]*a.hospital_demand_fraction for v in base)
    peak_policy=max(v[2]*a.hospital_demand_fraction for v in policy)
    return {'metrics':{'baseline_peak_hospital_demand':peak_base,'policy_peak_hospital_demand':peak_policy,
                       'policy_days_above_capacity':sum(v[2]*a.hospital_demand_fraction>a.hospital_capacity for v in policy[1:]),
                       'policy_peak_day':max(range(len(policy)),key=lambda day:policy[day][2]),
                       'maximum_population_balance_error':max(abs(sum(v)-a.population) for v in policy)},
            'rows':[{'day':day,'baseline_infectious':base[day][2],'policy_infectious':v[2],
                     'policy_susceptible':v[0],'policy_exposed':v[1],'policy_recovered':v[3],
                     'policy_hospital_demand':v[2]*a.hospital_demand_fraction} for day,v in enumerate(policy)]}


class DomainShock(Inputs):
    division: Label
    initial_shock: Annotated[float,Field(ge=-1,le=1)]


class Influence(Inputs):
    from_domain: Label
    to_domain: Label
    transmission_weight: Fraction


class CrossImpact(Inputs):
    shocks: list[DomainShock]=Field(min_length=1,max_length=13)
    links: list[Influence]=Field(default_factory=list,max_length=156)
    damping: Annotated[float,Field(ge=0,le=.95)]

    @model_validator(mode='after')
    def check(self):
        unique(self.shocks,'division');pairs=set();outgoing={d:0.0 for d in ALL_DOMAINS}
        if any(s.division not in ALL_DOMAINS for s in self.shocks):raise ValueError('Unknown shock division')
        for link in self.links:
            pair=(link.from_domain,link.to_domain)
            if link.from_domain not in ALL_DOMAINS or link.to_domain not in ALL_DOMAINS or pair in pairs or pair[0]==pair[1]:
                raise ValueError('Links need unique pairs of different GGISP divisions')
            pairs.add(pair);outgoing[link.from_domain]+=link.transmission_weight
        if any(v>1+1e-12 for v in outgoing.values()):raise ValueError('Outgoing transmission weights must sum to at most one per division')
        return self


def cross_impact(a):
    initial={d:0.0 for d in ALL_DOMAINS}
    for s in a.shocks:initial[s.division]=s.initial_shock
    values=dict(initial);converged=False
    for iteration in range(1,501):
        updated=dict(initial)
        for link in a.links:updated[link.to_domain]+=a.damping*link.transmission_weight*values[link.from_domain]
        difference=max(abs(updated[d]-values[d]) for d in ALL_DOMAINS)
        values=updated
        if difference<1e-10:converged=True;break
    return {'metrics':{'iterations':iteration,'converged':converged,
                       'largest_absolute_accumulated_score':max(abs(v) for v in values.values()),
                       'sum_absolute_accumulated_scores':sum(abs(v) for v in values.values())},
            'rows':[{'division':d,'direct_shock_score':initial[d],'accumulated_score':values[d],
                     'indirect_score':values[d]-initial[d]} for d in sorted(ALL_DOMAINS,key=lambda d:-abs(values[d]))]}


def advanced(domain,title,schema,fn,example,method,limits,applicable):
    item=entry(domain,title,schema,fn,example,method,limits)
    item.update(tier='advanced',applicable_domains=applicable)
    return item


ADVANCED_ENGINES={
 'robust-policy':advanced('development-finance','Robust policy choice under uncertainty',RobustChoice,robust,
    {'scenarios':[{'name':'Favorable','weight':1},{'name':'Adverse','weight':1}],
     'options':[{'name':'High upside','outcomes':[100,0]},{'name':'Resilient option','outcomes':[65,55]},{'name':'Weak option','outcomes':[30,20]}]},
    'Compare maximin, weighted-mean and minimax-regret choices; identify Pareto-dominated options. Higher scores are better. Regret is the gap to the best option within each scenario.',
    'Scenario scores must share units and a common higher-is-better direction. Weights are researcher assumptions, not estimated probabilities. Robustness covers only the entered scenarios.',ALL_DOMAINS),
 'voting-power':advanced('un-security-council','Coalition voting-power analysis',VotingPower,voting_power,
    {'players':[{'name':'Group A','weight':2,'veto':False},{'name':'Group B','weight':1,'veto':False},{'name':'Group C','weight':1,'veto':False}],'quota':3},
    'Exhaustively count coalitions and each player\'s losing-to-winning swings. Report absolute and normalized Banzhaf power, respecting configured veto players.',
    'At most 16 hypothetical players. Coalition enumeration treats possible membership patterns symmetrically; actual preferences, negotiation dynamics and current UN procedures are not modeled.',['un-security-council','wto-trade','international-tax']),
 'benchmark-audit':advanced('ai-governance','AI benchmark uncertainty and group audit',BenchmarkAudit,benchmark,
    {'groups':[{'name':'Evaluation group A','trials':100,'failures':3},{'name':'Evaluation group B','trials':40,'failures':4}],'failure_tolerance_percent':10},
    'Compute observed failure rates and two-sided 95% Wilson score intervals per group; compare interval upper bounds to a chosen tolerance. Show observed group-rate gap.',
    'Intervals assume independent binomial trials. They do not cover dataset shift, clustered prompts or multiple comparisons. Observed disparity alone does not establish discrimination or compliance.',['ai-governance','cybersecurity']),
 'stochastic-debt':advanced('sovereign-debt','Stochastic debt fan scenarios',StochasticDebt,stochastic_debt,
    {'initial_debt_percent_gdp':90,'mean_interest_percent':5,'mean_growth_percent':4,'primary_surplus_percent_gdp':1,
     'interest_std_pp':1,'growth_std_pp':2,'interest_growth_correlation':-.3,'breach_threshold_percent_gdp':100,'years':10,'simulations':500,'seed':42},
    'Seeded Monte Carlo debt paths with within-year correlated normal interest/growth shocks, independent across years. Report empirical 5/50/95 percentiles, terminal threshold frequency and worst-5% mean.',
    'Assumed distributions, not country calibration or an IMF DSA implementation. Interest draws are clipped to [-20,100]%, growth to [-95,200]%; clipping is counted. No default probability, exchange rates or fiscal feedback. Reproducibility depends on runtime as well as seed.',['sovereign-debt','development-finance','climate-finance']),
 'supply-network':advanced('critical-minerals','Supply-network bottleneck optimization',SupplyNetwork,supply_network,
    {'source':'Supply','sink':'Demand','required_throughput':12,'edges':[
      {'origin':'Supply','destination':'Port A','capacity':10,'disruption_percent':50},
      {'origin':'Supply','destination':'Port B','capacity':6,'disruption_percent':0},
      {'origin':'Port A','destination':'Demand','capacity':8,'disruption_percent':0},
      {'origin':'Port B','destination':'Demand','capacity':6,'disruption_percent':0}]},
    'Edmonds–Karp residual-network maximum flow before and after edge disruptions; identify the disrupted minimum cut and verify max-flow/min-cut agreement.',
    'Single divisible commodity with one source and sink, common capacity units and one period. No transit time, cost, inventory, substitution, multicommodity competition or actual routing instruction.',['critical-minerals','wto-trade','global-health','development-finance','ocean-governance']),
 'health-seir':advanced('global-health','Public-health SEIR scenario laboratory',SEIR,seir,
    {'population':100000,'initial_exposed':50,'initial_infectious':20,'reproduction_number':2,
     'incubation_days':5,'infectious_days':7,'intervention_day':20,'contact_reduction_percent':40,
     'hospital_demand_fraction':.05,'hospital_capacity':200,'days':120},
    'Compare baseline and contact-reduction SEIR paths using quarter-day exponential-hazard compartment transfers. Preserve population and nonnegative compartments; compare indicative capacity demand.',
    'Homogeneous synthetic population with constant assumed disease parameters. Demand is an infectious-stock proxy, not admissions or a clinical forecast. No age structure, births, deaths, waning, vaccination or calibration. Not for patient decisions.',['global-health']),
 'cross-impact':advanced('development-finance','Cross-domain impact propagation graph',CrossImpact,cross_impact,
    {'shocks':[{'division':'sovereign-debt','initial_shock':1}],
     'links':[{'from_domain':'sovereign-debt','to_domain':'development-finance','transmission_weight':.7},
              {'from_domain':'development-finance','to_domain':'global-health','transmission_weight':.5},
              {'from_domain':'development-finance','to_domain':'climate-finance','transmission_weight':.5}], 'damping':.7},
    'Iterate x = direct shock + damping × transposed weighted influence matrix × x. Outgoing weight sums ≤1 and damping ≤0.95 make the iteration contractive; report indirect scenario scores.',
    'An assumed linear influence graph, not causal inference. Signed scores are dimensionless, not harm probabilities. Links need empirical justification and expert review; propagation is not proof of a real cross-sector effect.',ALL_DOMAINS),
}

REFERENCES={
 'robust-policy':[('World Bank: robust investment decisions','https://ppp.worldbank.org/library/making-informed-investment-decisions-uncertain-world')],
 'voting-power':[("Banzhaf: account of the voting-power method",'https://www.banzhaf.net/accom.html')],
 'benchmark-audit':[('NIST: Wilson proportion intervals','https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm')],
 'stochastic-debt':[('IMF: debt sustainability and uncertainty','https://www.imf.org/en/About/FAQ/mac-dsa')],
 'supply-network':[('NetworkX: maximum-flow and minimum-cut methods','https://networkx.org/documentation/stable/reference/algorithms/flow.html')],
 'health-seir':[('CDC: infectious-disease transmission models','https://www.cdc.gov/cfa-modeling-and-forecasting/about/explainer-transmission-models.html')],
 'cross-impact':[('GGISP: explicitly defined contractive scenario model','/methods')],
}
for key,links in REFERENCES.items():
    ADVANCED_ENGINES[key]['references']=[{'title':title,'url':url} for title,url in links]
ADVANCED_ENGINES['robust-policy']['version']='1.0.1'
