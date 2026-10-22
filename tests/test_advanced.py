"""Independent known answers, invariants and rejection cases for advanced methods."""
from copy import deepcopy
import math

import pytest
from pydantic import ValidationError

from ggisp.engines import ENGINES,calculate_engine
from ggisp.advanced import ADVANCED_ENGINES,wilson
from ggisp.db import DOMAINS


def calculate(key,params=None):
    return calculate_engine(key,params if params is not None else ENGINES[key]['example'])[1]


def test_advanced_applicability_covers_all_thirteen_divisions():
    assert len(ADVANCED_ENGINES)==7
    assert set(ENGINES['robust-policy']['applicable_domains'])=={d[0] for d in DOMAINS}
    assert set(ENGINES['cross-impact']['applicable_domains'])=={d[0] for d in DOMAINS}


def test_minimax_regret_and_pareto_known_answer():
    out=calculate('robust-policy')
    assert out['metrics']['minimax_regret_choice']=='Resilient option'
    assert out['metrics']['minimax_regret']==35
    assert next(r for r in out['rows'] if r['option']=='Weak option')['pareto_dominated']
    assert out['metrics']['pareto_efficient_options']==2


def test_robust_options_require_matching_scenario_dimensions():
    p=deepcopy(ENGINES['robust-policy']['example']);p['options'][0]['outcomes']=[1]
    with pytest.raises(ValidationError):calculate('robust-policy',p)


def test_robust_ties_are_explicit():
    p=deepcopy(ENGINES['robust-policy']['example']);p['options'][0]['outcomes']=[120,0]
    metrics=calculate('robust-policy',p)['metrics']
    assert metrics['minimax_regret_tied_options']==2
    assert metrics['minimax_regret_choice']=='Resilient option'
    assert metrics['weighted_mean_choice']=='High upside; Resilient option'
    p=deepcopy(ENGINES['robust-policy']['example'])
    for scenario in p['scenarios']:scenario['weight']=0
    with pytest.raises(ValidationError):calculate('robust-policy',p)


def test_banzhaf_known_weighted_game():
    out=calculate('voting-power')
    assert [r['critical_swings'] for r in out['rows']]==[3,1,1]
    assert [r['normalized_banzhaf_power'] for r in out['rows']]==pytest.approx([.6,.2,.2])
    assert sum(r['normalized_banzhaf_power'] for r in out['rows'])==pytest.approx(1)


def test_veto_can_create_a_dictator_in_hypothetical_game():
    p={'quota':1,'players':[{'name':'Veto','weight':1,'veto':True},{'name':'Other','weight':5,'veto':False}]}
    rows=calculate('voting-power',p)['rows']
    assert rows[0]['normalized_banzhaf_power']==1
    assert rows[1]['normalized_banzhaf_power']==0


def test_wilson_zero_failures_is_not_zero_upper_bound():
    lower,upper=wilson(0,100)
    assert lower==pytest.approx(0,abs=1e-12)
    assert upper==pytest.approx(.0369935,abs=1e-6)
    lower,upper=wilson(100,100)
    assert upper==pytest.approx(1)
    assert lower==pytest.approx(1-.0369935,abs=1e-6)


def test_audit_group_denominator_and_tolerance():
    p={'groups':[{'name':'Small sample','trials':10,'failures':0}],'failure_tolerance_percent':5}
    assert calculate('benchmark-audit',p)['rows'][0]['upper_bound_within_tolerance'] is False
    p['groups'][0]['failures']=11
    with pytest.raises(ValidationError):calculate('benchmark-audit',p)


def test_stochastic_debt_zero_volatility_collapses_to_identity():
    p={**ENGINES['stochastic-debt']['example'],'mean_interest_percent':5,'mean_growth_percent':5,
       'primary_surplus_percent_gdp':0,'interest_std_pp':0,'growth_std_pp':0,'simulations':20}
    out=calculate('stochastic-debt',p)
    for row in out['rows']:
        assert row['p05_debt_percent_gdp']==pytest.approx(90)
        assert row['median_debt_percent_gdp']==pytest.approx(90)
        assert row['p95_debt_percent_gdp']==pytest.approx(90)
    assert out['metrics']['terminal_threshold_exceedance_fraction']==0


def test_stochastic_seed_quantiles_and_nonmutation():
    p=deepcopy(ENGINES['stochastic-debt']['example']);original=deepcopy(p)
    a=calculate('stochastic-debt',p);b=calculate('stochastic-debt',p)
    assert a==b and p==original
    assert all(r['p05_debt_percent_gdp']<=r['median_debt_percent_gdp']<=r['p95_debt_percent_gdp'] for r in a['rows'])
    c=calculate('stochastic-debt',{**p,'seed':43})
    assert a['rows']!=c['rows']


def test_stochastic_extreme_correlation_is_finite():
    for rho in [-1,1]:
        p={**ENGINES['stochastic-debt']['example'],'interest_growth_correlation':rho,'simulations':20}
        assert math.isfinite(calculate('stochastic-debt',p)['metrics']['mean_of_worst_five_percent'])


def test_maxflow_min_cut_disruption_known_answer():
    out=calculate('supply-network')
    assert out['metrics']['baseline_maximum_throughput']==14
    assert out['metrics']['disrupted_maximum_throughput']==11
    assert out['metrics']['disrupted_minimum_cut_capacity']==11
    assert out['metrics']['unmet_required_throughput']==1


def test_flow_conservation_and_capacity_with_antiparallel_edges():
    p={'source':'S','sink':'T','required_throughput':10,'edges':[
        {'origin':'S','destination':'A','capacity':5,'disruption_percent':0},
        {'origin':'A','destination':'S','capacity':2,'disruption_percent':0},
        {'origin':'A','destination':'T','capacity':4,'disruption_percent':0},
        {'origin':'S','destination':'T','capacity':3,'disruption_percent':0}]}
    out=calculate('supply-network',p)
    assert out['metrics']['disrupted_maximum_throughput']==7
    rows=out['rows'];balance={n:0 for n in ['S','A','T']}
    for r in rows:
        assert 0<=r['disrupted_flow']<=r['disrupted_capacity']
        balance[r['origin']]-=r['disrupted_flow'];balance[r['destination']]+=r['disrupted_flow']
    assert balance['A']==pytest.approx(0)
    assert balance['T']==pytest.approx(7)


def test_flow_disconnected_and_duplicate_rejected():
    p=deepcopy(ENGINES['supply-network']['example'])
    for e in p['edges']:e['disruption_percent']=100
    assert calculate('supply-network',p)['metrics']['disrupted_maximum_throughput']==0
    p['edges'].append(dict(p['edges'][0]))
    with pytest.raises(ValidationError):calculate('supply-network',p)


def test_seir_conservation_nonnegative_and_zero_infection():
    out=calculate('health-seir')
    for r in out['rows']:
        assert all(r[k]>=0 for k in ['policy_susceptible','policy_exposed','policy_infectious','policy_recovered'])
        assert sum(r[k] for k in ['policy_susceptible','policy_exposed','policy_infectious','policy_recovered'])==pytest.approx(100000)
    p={**ENGINES['health-seir']['example'],'initial_exposed':0,'initial_infectious':0}
    assert calculate('health-seir',p)['metrics']['policy_peak_hospital_demand']==0


def test_seir_no_intervention_produces_identical_paths():
    p={**ENGINES['health-seir']['example'],'contact_reduction_percent':0}
    assert all(r['baseline_infectious']==r['policy_infectious'] for r in calculate('health-seir',p)['rows'])


def test_seir_initial_compartments_cannot_exceed_population():
    with pytest.raises(ValidationError):calculate('health-seir',{**ENGINES['health-seir']['example'],'population':1})


def test_cross_impact_chain_closed_form():
    out=calculate('cross-impact');rows={r['division']:r for r in out['rows']}
    assert rows['development-finance']['accumulated_score']==pytest.approx(.49)
    assert rows['global-health']['accumulated_score']==pytest.approx(.1715)
    assert rows['climate-finance']['accumulated_score']==pytest.approx(.1715)
    assert out['metrics']['converged']


def test_cross_impact_cycle_converges_to_analytic_solution():
    p={'shocks':[{'division':'global-health','initial_shock':1}], 'damping':.5,'links':[
        {'from_domain':'global-health','to_domain':'climate-finance','transmission_weight':1},
        {'from_domain':'climate-finance','to_domain':'global-health','transmission_weight':1}]}
    rows={r['division']:r for r in calculate('cross-impact',p)['rows']}
    assert rows['global-health']['accumulated_score']==pytest.approx(4/3)
    assert rows['climate-finance']['accumulated_score']==pytest.approx(2/3)
    p['links'][0]['transmission_weight']=1.1
    with pytest.raises(ValidationError):calculate('cross-impact',p)
