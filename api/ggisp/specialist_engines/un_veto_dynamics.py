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

    # Institutional Reform Architecture (Kovtun & Havlakov 2025; Gould & Rablen 2017; He et al. 2026)
    reform_model: str = Field(
        default="status_quo",
        description="Reform proposal model: status_quo, g4_expansion, model_b_semi_permanent, double_veto_rule, elected_expansion_only"
    )
    un_general_assembly_sponsorship_votes: int = Field(
        default=122, ge=0, le=193, description="Estimated UN General Assembly votes supporting the draft resolution/amendment"
    )


def simulate_unsc_voting(inp: UNSCVotingInput) -> Dict[str, Any]:
    """Calculate UNSC passage probability, veto risks, UNGA Res 377A referral likelihood, and reform model dynamics."""
    p5_names = ["United States", "United Kingdom", "France", "Russian Federation", "China"]
    p5_probs = [inp.us_veto_prob, inp.uk_veto_prob, inp.fr_veto_prob, inp.ru_veto_prob, inp.cn_veto_prob]

    # Model reform-specific voting rules:
    reform = inp.reform_model.lower().strip()

    # 1. Negative Voting Blockage Calculation
    if reform == "double_veto_rule":
        # Requires >= 2 concurring negative permanent votes to block (He et al. 2026; Gould & Rablen 2017)
        # Prob of blockage = Sum_{i<j} p_i * p_j (for independent draws approximation)
        prob_veto_any = 0.0
        for i in range(len(p5_probs)):
            for j in range(i + 1, len(p5_probs)):
                prob_veto_any += p5_probs[i] * p5_probs[j]
        prob_veto_any = min(prob_veto_any, 0.95)
        prob_no_veto = 1.0 - prob_veto_any
        veto_rule_description = "Double Veto Threshold: Requires >= 2 concurring permanent negative votes to veto."
    else:
        # Standard Single-Veto Status Quo (Article 27.3)
        prob_no_veto = 1.0
        for p in p5_probs:
            prob_no_veto *= (1.0 - p)
        prob_veto_any = 1.0 - prob_no_veto
        veto_rule_description = "Single P5 Veto: Any single permanent member negative vote blocks resolution."

    veto_contributors = {name: f"{round(p * 100, 1)}%" for name, p in zip(p5_names, p5_probs)}

    # 2. Affirmative Voting Thresholds across Structural Models (Chen et al. 2022; Gould & Rablen 2017):
    if reform == "g4_expansion":
        total_council_seats = 25
        required_affirmative_threshold = 15  # ~60% majority of 25
        estimated_p5_yes = sum(1 for p in p5_probs if p < 0.20)
        # G4 + elected seats support expansion
        total_affirmative = inp.e10_affirmative_votes + estimated_p5_yes + 4
        ss_p5_power = 11.2
        ss_elected_power = 0.44
        reform_evaluation = (
            "G4 EXPANSION (25 seats): Enlarges regional legitimacy (+6 permanent without immediate veto, +4 elected). "
            "Decision modeling indicates higher resolution throughput if new permanent members accept veto moratorium."
        )
    elif reform == "model_b_semi_permanent":
        total_council_seats = 24
        required_affirmative_threshold = 14
        estimated_p5_yes = sum(1 for p in p5_probs if p < 0.20)
        total_affirmative = inp.e10_affirmative_votes + estimated_p5_yes + 3
        ss_p5_power = 14.8
        ss_elected_power = 0.38
        reform_evaluation = (
            "MODEL B SEMI-PERMANENT (24 seats): 8 renewable 4-year seats expand regional presence without creating "
            "new permanent veto players, preserving decision efficiency (Chen et al. 2022)."
        )
    elif reform == "double_veto_rule":
        total_council_seats = 15
        required_affirmative_threshold = 9
        estimated_p5_yes = sum(1 for p in p5_probs if p < 0.20)
        total_affirmative = inp.e10_affirmative_votes + estimated_p5_yes
        ss_p5_power = 12.4
        ss_elected_power = 3.8
        reform_evaluation = (
            "DOUBLE VETO SYSTEM (15 seats): Substantially rebalances equity and efficiency by eliminating single-power "
            "obstruction on Chapter VII humanitarian mandates (He et al. 2026; Gould & Rablen 2017)."
        )
    else:  # status_quo or elected_expansion_only
        total_council_seats = 15
        required_affirmative_threshold = 9
        estimated_p5_yes = sum(1 for p in p5_probs if p < 0.20)
        total_affirmative = inp.e10_affirmative_votes + estimated_p5_yes
        ss_p5_power = 19.63
        ss_elected_power = 0.185
        reform_evaluation = (
            "STATUS QUO (15 seats): Asymmetric power lock-in (1945 distribution); P5 wields 98.1% collective Shapley-Shubik voting power."
        )

    meets_affirmative_threshold = total_affirmative >= required_affirmative_threshold
    passage_prob = prob_no_veto if meets_affirmative_threshold else 0.0

    # 3. UN Charter Article 108 Amendment Feasibility (Hosli & Dörfler 2019; Mehmeti 2026):
    # Requires 2/3 GA majority (>= 129 of 193) AND ratification by all 5 permanent members.
    ga_two_thirds_met = inp.un_general_assembly_sponsorship_votes >= 129
    p5_consensus_for_amendment = all(p < 0.30 for p in p5_probs)
    article_108_status = (
        "RATIFICATION BLOCKED: Even with a 2/3 GA majority, divergent P5 strategic interests (Western support vs. Sino-Russian "
        "resistance to specific candidates) activate individual ratification vetoes under Article 108 (Mehmeti 2026)."
        if not p5_consensus_for_amendment
        else "RATIFICATION PATHWAY OPEN: P5 alignment achieved for formal Charter amendment under Article 108."
    )

    # General Assembly Resolution 377(V) 'Uniting for Peace' referral threshold:
    uniting_for_peace_prob = prob_veto_any if inp.resolution_type in ("chapter_vii_sanctions", "peacekeeping") else 0.0

    return {
        "engine": "UN Security Council Veto & Coalition Dynamics Engine",
        "domain": "un-security-council",
        "reform_model": reform,
        "resolution_type": inp.resolution_type,
        "council_composition": {
            "total_seats": total_council_seats,
            "affirmative_vote_threshold": required_affirmative_threshold,
            "estimated_affirmative_votes": total_affirmative,
            "veto_rule": veto_rule_description,
        },
        "meets_procedural_9_vote_rule": meets_affirmative_threshold,
        "probability_of_veto_blockage_percent": round(prob_veto_any * 100, 1),
        "probability_of_resolution_adoption_percent": round(passage_prob * 100, 1),
        "veto_risk_breakdown_by_p5": veto_contributors,
        "shapley_shubik_power_distribution": {
            "p5_permanent_member_power_percent": ss_p5_power,
            "e10_elected_member_power_percent": ss_elected_power,
            "p5_collective_dominance_percent": round(ss_p5_power * 5, 1),
        },
        "article_108_amendment_feasibility": {
            "ga_two_thirds_majority_secured": ga_two_thirds_met,
            "all_p5_ratification_expected": p5_consensus_for_amendment,
            "institutional_prognosis": article_108_status,
        },
        "un_general_assembly_emergency_referral_likelihood_percent": round(uniting_for_peace_prob * 100, 1),
        "institutional_reform_assessment": reform_evaluation,
        "diplomatic_recommendation": (
            "High veto risk detected. Implement incremental working reforms (Liechtenstein Veto Initiative public justification, "
            "General Assembly Res 377A referral, and Chapter VIII regional delegation) to bypass Article 108 deadlock."
            if prob_veto_any > 0.50
            else "Favorable conditions for consensus adoption; consolidate cross-regional E10 support."
        ),
        "literature_citations": [
            "Kovtun, O., & Havlakov, K. (2025). Actual Problems of International Relations, 10.17721/apmv.2025.164.1.76-84",
            "Mehmeti, R. M. (2026). Sci. J. Nat. Acad. Internal Affairs, 10.63341/naia-herald/2.2026.70",
            "Gould, M., & Rablen, M. D. (2017). Public Choice, 10.1007/s11127-017-0468-2",
            "He, W. et al. (2026). LN Educational Psychology & Public Media, 10.54254/2753-7048/2025.31980",
            "Hosli, M., & Dörfler, T. (2019). J. Economic Policy Reform, 10.1080/17487870.2017.1305903",
            "Chen, C. et al. (2022). SHS Web of Conferences, 10.1051/shsconf/202214803004"
        ]
    }

