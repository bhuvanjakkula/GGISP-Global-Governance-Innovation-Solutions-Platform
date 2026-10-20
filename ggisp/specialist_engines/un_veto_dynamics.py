"""Specialist Engine 2: UN Security Council Veto Dynamics & Voting Coalition Model.
Reference: UN Charter Chapter VII / Shapley-Shubik Power Indices / Resolution 377A.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class UNSCVotingInput(BaseModel):
    resolution_type: str = Field(default="chapter_vii_sanctions", description="Resolution category: procedural, chapter_vi, chapter_vii_sanctions, peacekeeping")
    sponsoring_bloc: str = Field(default="Western Allies", description="Sponsoring group")
    e10_affirmative_votes: int = Field(default=7, ge=0, le=10, description="Estimated affirmative votes among 10 elected members")
    us_veto_prob: float = Field(default=0.05, ge=0.0, le=1.0)
    uk_veto_prob: float = Field(default=0.05, ge=0.0, le=1.0)
    fr_veto_prob: float = Field(default=0.05, ge=0.0, le=1.0)
    ru_veto_prob: float = Field(default=0.75, ge=0.0, le=1.0)
    cn_veto_prob: float = Field(default=0.45, ge=0.0, le=1.0)


def simulate_unsc_voting(inp: UNSCVotingInput) -> Dict[str, Any]:
    """Calculate UNSC passage probability, veto risks, and UNGA Resolution 377A referral likelihood."""
    # Under UNSC rules (Article 27.3): Passage requires >= 9 affirmative votes AND 0 permanent vetoes.
    p5_names = ["United States", "United Kingdom", "France", "Russian Federation", "China"]
    p5_probs = [inp.us_veto_prob, inp.uk_veto_prob, inp.fr_veto_prob, inp.ru_veto_prob, inp.cn_veto_prob]

    # Probability of zero vetoes: product of (1 - p_veto)
    prob_no_veto = 1.0
    veto_contributors = {}
    for name, p in zip(p5_names, p5_probs):
        prob_no_veto *= (1.0 - p)
        veto_contributors[name] = f"{round(p * 100, 1)}%"

    prob_veto_any = 1.0 - prob_no_veto

    # Voting threshold: Need >= 9 affirmative votes out of 15
    # P5 non-vetoing members typically vote yes or abstain
    estimated_p5_yes = sum(1 for p in p5_probs if p < 0.20)
    total_affirmative = inp.e10_affirmative_votes + estimated_p5_yes
    meets_nine_vote_threshold = total_affirmative >= 9

    # Overall passage probability
    passage_prob = prob_no_veto if meets_nine_vote_threshold else 0.0

    # Shapley-Shubik Voting Power:
    # Under classical cooperative game theory with 5 permanent and 10 non-permanent members:
    # A single P5 member has ~19.6% power, while an E10 member has ~0.19% power.
    ss_p5_power = 19.63
    ss_e10_power = 0.185

    # General Assembly Resolution 377(V) 'Uniting for Peace' referral threshold:
    # When UNSC fails due to lack of unanimity among permanent members, UNGA can convene in Emergency Special Session.
    uniting_for_peace_prob = prob_veto_any if inp.resolution_type in ("chapter_vii_sanctions", "peacekeeping") else 0.0

    return {
        "engine": "UN Security Council Veto & Coalition Dynamics Engine",
        "domain": "un-security-council",
        "resolution_type": inp.resolution_type,
        "estimated_total_affirmative_votes": total_affirmative,
        "meets_procedural_9_vote_rule": meets_nine_vote_threshold,
        "probability_of_veto_blockage_percent": round(prob_veto_any * 100, 1),
        "probability_of_resolution_adoption_percent": round(passage_prob * 100, 1),
        "veto_risk_breakdown_by_p5": veto_contributors,
        "shapley_shubik_power_distribution": {
            "p5_permanent_member_power_percent": ss_p5_power,
            "e10_elected_member_power_percent": ss_e10_power,
            "p5_collective_dominance_percent": round(ss_p5_power * 5, 1),
        },
        "un_general_assembly_emergency_referral_likelihood_percent": round(uniting_for_peace_prob * 100, 1),
        "diplomatic_recommendation": (
            "High veto risk detected. Recommend pre-consultation compromise packaging or parallel General Assembly Emergency Session (Res 377A) referral."
            if prob_veto_any > 0.50
            else "Favorable conditions for consensus adoption; consolidate E10 non-aligned support."
        ),
    }
