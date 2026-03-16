"""
VerifyLayer — Main orchestrator for the verification pipeline.

Coordinates fact extraction, NLI verification, contradiction detection,
and confidence scoring into a single async pipeline that completes
within the 200ms latency budget.

Usage:
    from verification.verifylayer import verify_layer

    response = await verify_layer.verify_utterance(
        incident_id="INC-001",
        caller_id="caller-1",
        caller_role="witness",
        agent_id="agent-1",
        utterance="There's a red car on fire on Main Street",
    )
"""
import time
import logging
import asyncio
from typing import Optional

from core.config import settings
from verification.models import (
    ExtractedFact,
    VerificationResult,
    VerifyUtteranceResponse,
    NLILabel,
)
from verification.nli_engine import NLIEngine
from verification.contradiction import ContradictionDetector
from verification.penalization import PenalizationEngine
from verification.cache import AsyncLRUCache

logger = logging.getLogger("nexus911.verifylayer")


class VerifyLayer:
    """
    Main verification pipeline orchestrator.

    Pipeline per fact:
    1. Check cache → return immediately if hit
    2. NLI verification against known premises
    3. Cross-caller contradiction check
    4. Confidence scoring with penalization
    5. Cache result and return
    """

    def __init__(self):
        self.nli = NLIEngine()
        self.contradictions = ContradictionDetector()
        self.penalization = PenalizationEngine()
        self.cache = AsyncLRUCache(max_size=1024, ttl_seconds=300.0)
        self._premises: dict[str, str] = {}  # incident_id -> accumulated premises

    async def verify_utterance(
        self,
        incident_id: str,
        caller_id: str,
        caller_role: str = "unknown",
        agent_id: str = "",
        utterance: str = "",
        facts: Optional[list[str]] = None,
    ) -> VerifyUtteranceResponse:
        """
        Full verification pipeline for a caller utterance.

        Extracts facts (or uses provided ones), runs them through
        NLI + contradiction + scoring, and returns results.
        """
        start = time.time()

        # Step 1: Extract facts from utterance if not provided
        if facts is None:
            facts = await self.nli.extract_facts(utterance)

        # Step 2: Create ExtractedFact objects
        extracted = [
            ExtractedFact(
                incident_id=incident_id,
                caller_id=caller_id,
                caller_role=caller_role,
                agent_id=agent_id,
                fact_text=f,
            )
            for f in facts
        ]

        # Step 3: Verify each fact (concurrently)
        tasks = [self._verify_single(fact) for fact in extracted]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        verified = []
        for result in results:
            if isinstance(result, VerificationResult):
                verified.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Fact verification error: {result}")

        elapsed_ms = (time.time() - start) * 1000

        return VerifyUtteranceResponse(
            incident_id=incident_id,
            caller_id=caller_id,
            results=verified,
            latency_ms=round(elapsed_ms, 2),
        )

    async def _verify_single(self, fact: ExtractedFact) -> VerificationResult:
        """Verify a single extracted fact through the full pipeline."""

        # 1. Cache check
        cached = await self.cache.get(fact.fact_id)
        if cached:
            return cached

        # 2. Get premise for this incident
        premise = self._premises.get(fact.incident_id, "")

        # 3. NLI verification
        nli_result = await self.nli.verify(
            premise=premise,
            hypothesis=fact.fact_text,
        )

        # 4. Contradiction check
        contradiction_reports = await self.contradictions.check_contradictions(fact)

        # 5. Register fact for future contradiction checks
        self.contradictions.register_fact(fact)

        # 6. Count corroborating callers
        existing_facts = self.contradictions.get_incident_facts(fact.incident_id)
        corroborating = len(set(
            f.caller_id for f in existing_facts
            if f.caller_id != fact.caller_id
            and f.fact_text.lower().strip() == fact.fact_text.lower().strip()
        ))

        # 7. Confidence scoring
        confidence = self.penalization.score(
            nli_result=nli_result,
            caller_role=fact.caller_role,
            contradictions=contradiction_reports,
            corroborating_callers=corroborating,
        )

        result = VerificationResult(
            fact=fact,
            nli=nli_result,
            confidence=confidence,
            contradictions=contradiction_reports,
        )

        # 8. Cache result
        await self.cache.put(fact.fact_id, result)

        # 9. Update premise for this incident (entailed facts become premises)
        if nli_result.label == NLILabel.ENTAILMENT:
            self._premises[fact.incident_id] = (
                f"{premise} {fact.fact_text}".strip()
            )

        return result

    async def get_incident_intel(
        self,
        incident_id: str,
        agent_id: str = "",
    ) -> dict:
        """Get all verified facts for an incident, optionally filtered by agent."""
        facts = self.contradictions.get_incident_facts(incident_id)

        if agent_id:
            facts = [f for f in facts if f.agent_id == agent_id]

        return {
            "incident_id": incident_id,
            "agent_id": agent_id,
            "facts": [f.model_dump() for f in facts],
            "total": len(facts),
        }


# Module-level singleton
verify_layer = VerifyLayer()
