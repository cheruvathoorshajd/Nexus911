"""
Penalization Engine — Confidence scoring with caller credibility weighting.

Computes composite confidence scores for verified facts by combining:
- NLI verification score
- Caller role credibility weight
- Cross-caller agreement bonus
- Contradiction penalty

Caller credibility weights are based on emergency response research:
officials > victims > witnesses > bystanders > children > unknown.
"""
import logging
from verification.models import (
    FactConfidence,
    NLIResult,
    NLILabel,
    ContradictionReport,
    CallerRole,
)

logger = logging.getLogger("nexus911.verifylayer.penalization")

# Credibility weights by caller role (based on 911 dispatch research)
CALLER_CREDIBILITY = {
    CallerRole.OFFICIAL: 0.95,          # Police, fire, EMS on scene
    CallerRole.VICTIM: 0.75,            # Direct involvement, but stress affects accuracy
    CallerRole.WITNESS: 0.65,           # Eyewitness, moderate reliability
    CallerRole.REPORTING_PARTY: 0.60,   # Reporting from nearby, reasonable reliability
    CallerRole.INVOLVED_PARTY: 0.60,    # Involved but not primary victim/witness
    CallerRole.BYSTANDER: 0.50,         # Less direct observation
    CallerRole.REPEAT_CALLER: 0.40,     # May be unreliable or escalatory
    CallerRole.CHILD: 0.35,             # Limited reliability, but important signals
    CallerRole.UNKNOWN: 0.50,           # Default
}


class PenalizationEngine:
    """Computes composite confidence scores for verified facts."""

    def score(
        self,
        nli_result: NLIResult,
        caller_role: str,
        contradictions: list[ContradictionReport],
        corroborating_callers: int = 0,
    ) -> FactConfidence:
        """
        Compute composite confidence score.

        Args:
            nli_result: NLI verification result.
            caller_role: Role of the caller (victim, witness, etc.)
            contradictions: Any contradictions found.
            corroborating_callers: Number of other callers who said the same thing.

        Returns:
            FactConfidence with component scores and overall.
        """
        # 1. NLI score
        if nli_result.label == NLILabel.ENTAILMENT:
            nli_score = nli_result.score
        elif nli_result.label == NLILabel.CONTRADICTION:
            nli_score = -nli_result.score
        else:
            nli_score = 0.0

        # 2. Caller credibility
        # Handle both uppercase (incident graph) and lowercase (verification) role values
        role_str = caller_role.lower() if caller_role else "unknown"
        try:
            role_enum = CallerRole(role_str)
        except ValueError:
            role_enum = CallerRole.UNKNOWN
        caller_credibility = CALLER_CREDIBILITY.get(role_enum, 0.5)

        # 3. Cross-caller agreement bonus
        agreement_bonus = min(corroborating_callers * 0.1, 0.3)  # Max 30% bonus

        # 4. Contradiction penalty
        if contradictions:
            max_severity = max(c.severity for c in contradictions)
            contradiction_penalty = max_severity * 0.5  # Up to 50% penalty
        else:
            contradiction_penalty = 0.0

        # Composite: weighted combination
        overall = (
            (nli_score * 0.4)
            + (caller_credibility * 0.3)
            + (agreement_bonus * 0.2)
            - (contradiction_penalty * 0.1)
        )
        overall = max(0.0, min(1.0, overall))  # Clamp to [0, 1]

        return FactConfidence(
            nli_score=round(nli_score, 4),
            caller_credibility=round(caller_credibility, 4),
            cross_caller_agreement=round(agreement_bonus, 4),
            contradiction_penalty=round(contradiction_penalty, 4),
            overall=round(overall, 4),
        )
