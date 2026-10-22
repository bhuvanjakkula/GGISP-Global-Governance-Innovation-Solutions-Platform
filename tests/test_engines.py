"""Known-answer and conservation checks for the analytical methods."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from ggisp.db import DOMAINS
from ggisp.engines import ENGINES, calculate_engine


def calculate(engine, params=None):
    return calculate_engine(engine, params if params is not None else ENGINES[engine]['example'])[1]


def test_one_working_engine_per_division():
    assert {e['domain'] for e in ENGINES.values()} == {d[0] for d in DOMAINS}
    assert len(ENGINES)==20


@pytest.mark.parametrize('engine',list(ENGINES))
def test_each_catalog_example_calculates_deterministically(engine):
    out=calculate(engine)
    assert out==calculate(engine)
    assert out['metrics'] and out['method'] and out['limitations']


def test_weighted_safeguards_known_answer():
    assert calculate('safeguards')['metrics']['weighted_coverage_percent']==38


def test_veto_and_threshold_are_separate():
    p=deepcopy(ENGINES['voting']['example'])
    assert calculate('voting',p)['metrics']['passes'] is False
    p['veto_enabled']=False
    assert calculate('voting',p)['metrics']['passes'] is True
    p['required_share_percent']=81
    assert calculate('voting',p)['metrics']['passes'] is False


def test_tariff_fixed_basket_known_answer():
    assert calculate('trade')['metrics']['duty_change']==-50000


def test_ai_risk_mitigation_known_answer():
    assert calculate('ai-assurance')['metrics']['residual_score']==pytest.approx(4.56)


def test_defensive_investment_economics():
    out=calculate('cyber-loss')['metrics']
    assert out['residual_expected_annual_loss']==90000
    assert out['net_expected_annual_benefit']==80000


@pytest.mark.parametrize('available',[0,1,50,100,1000])
def test_allocation_conserves_supply_and_respects_caps(available):
    out=calculate('health-allocation',{'available_units':available,'regions':[
        {'name':'A','unmet_need':10,'vulnerability_weight':100},
        {'name':'B','unmet_need':90,'vulnerability_weight':1}]})
    assert out['metrics']['allocated_units']==pytest.approx(min(available,100))
    assert out['metrics']['unused_units']+out['metrics']['allocated_units']==pytest.approx(available)
    assert all(r['unmet_after']>=0 for r in out['rows'])
    assert out['rows'][0]['allocated']<=10


def test_zero_need_allocation_is_finite():
    out=calculate('health-allocation',{'available_units':50,'regions':[{'name':'A','unmet_need':0,'vulnerability_weight':1}]})
    assert out['metrics']['unused_units']==50


def test_space_expectation():
    assert calculate('space-disposal')['metrics']['expected_failed_disposals']==pytest.approx(20)


def test_supply_concentration_and_shortfall():
    assert calculate('minerals')['metrics']=={'concentration_hhi':5200,'disrupted_share_percent':60,'uncovered_shortfall_percent':40}
    p=deepcopy(ENGINES['minerals']['example']);p['suppliers'][0]['share_percent']=59
    with pytest.raises(ValidationError): calculate('minerals',p)


def test_pollution_mass_balance_and_cleanup_cap():
    assert calculate('ocean')['metrics']['terminal_pollution_tonnes']==700
    out=calculate('ocean',{'initial_pollution_tonnes':10,'annual_inflow_tonnes':0,'prevention_percent':0,'annual_cleanup_capacity_tonnes':100,'years':2})
    assert out['metrics']['terminal_pollution_tonnes']==0
    assert out['metrics']['removed_tonnes']==10


def test_fiscal_revenue_known_answer():
    assert calculate('tax')['metrics']['net_revenue_change']==110000


def investment(name,cost,benefit,requires=None):
    return {'name':name,'division':'global-health','cost':cost,'benefit_score':benefit,
            'delivery_probability':1,'equity_multiplier':1,'requires':requires or []}


def test_optimizer_beats_greedy_ratio():
    out=calculate('portfolio',{'budget':10,'investments':[
        investment('A',6,12),investment('B',5,9),investment('C',5,9)]})
    assert out['metrics']['selected_score']==18
    assert {r['investment'] for r in out['rows'] if r['selected']}=={'B','C'}


def test_optimizer_dependencies_synergies_and_empty_budget():
    p={'budget':10,'investments':[investment('A',5,1),investment('B',5,10,['A']),investment('C',10,12)],
       'synergies':[{'first':'A','second':'B','benefit_score':3}]}
    assert calculate('portfolio',p)['metrics']['selected_score']==14
    p['budget']=0
    assert calculate('portfolio',p)['metrics']['selected_count']==0
    p['investments'][0]['requires']=['B']
    with pytest.raises(ValidationError): calculate('portfolio',p)


def test_optimizer_prefers_lower_cost_on_tie():
    p={'budget':10,'investments':[investment('A',10,10),investment('B',9,10)]}
    assert calculate('portfolio',p)['metrics']['spent']==9


def test_climate_zero_reduction_no_division_by_zero():
    assert calculate('climate')['metrics']['cost_per_avoided_tonne']==50
    p={**ENGINES['climate']['example'],'reduction_percent':0}
    assert calculate('climate',p)['metrics']['cost_per_avoided_tonne'] is None


def test_duplicate_and_unknown_fields_rejected():
    p=deepcopy(ENGINES['trade']['example']);p['items'][1]['name']=p['items'][0]['name']
    with pytest.raises(ValidationError):calculate('trade',p)
    p={**ENGINES['cyber-loss']['example'],'made_up_parameter':7}
    with pytest.raises(ValidationError):calculate('cyber-loss',p)


def test_nonfinite_and_explosive_debt_rejected():
    with pytest.raises(ValidationError):calculate('climate',{**ENGINES['climate']['example'],'annual_program_cost':float('inf')})
    with pytest.raises(ValidationError):calculate('debt',{**ENGINES['debt']['example'],'nominal_gdp_growth_percent':-99.9999,'years':30})
