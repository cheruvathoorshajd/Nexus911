"""
Cross-Call Contradiction Detector.

When multiple agents handle the same incident, compares facts from
different callers. If Agent 1's child caller says "red car" and
Agent 2's witness says "blue Honda," this module flags the contradiction.

Uses Gemini 2.0 Flash for semantic contradiction detection — simple
keyword overlap is insufficient for emergency contexts.
"""
import json
import logging
import asyncio
from typing import Optional

from google import genai

from core.config import settings
from verification.models import (
    ExtractedFact,
    ContradictionReport,
)

logger = logging.getLogger("nexus911.verifylayer.contradiction")

CONTRADICTION_MODEL = "gemini-2.5-flash"

CONTRADICTION_PROMPT = """You are a contradiction detector for a 911 emergency system.

Given two facts from DIFFERENT callers about the SAME incident, determine if they contradict each other.

Consider:
- Direct contradictions (red car vs blue car)
- Temporal contradictions (suspect left vs suspect still here)
- Quantity contradictions (2 victims vs 5 victims)
- Location contradictions (front yard vs backyard)

Do NOT flag as contradictions:
- Complementary information (one says "red shirt", other says "wearing jeans" — both can be true)
- Different levels of detail (one says "car", other says "blue Honda Civic")
- Subjective differences in emotional descriptions

Respond ONLY with JSON:
{
    "is_contradiction": true | false,
    "severity": 0.0 to 1.0,
    "contradiction_type": "direct" | "temporal" | "quantity" | "location" | "none",
    "explanation": "Brief explanation"
}"""


class ContradictionDetector:
    """Detects contradictions between facts from different callers."""

    def __init__(self, api_key: str = ""):
        from core.config import create_genai_client
        self._client = create_genai_client()
        # In-memory store of verified facts per incident for comparison
        self._incident_facts: dict[str, list[ExtractedFact]] = {}

    def register_fact(self, fact: ExtractedFact):
        """Register a verified fact for future contradiction checks."""
        if fact.incident_id not in self._incident_facts:
            self._incident_facts[fact.incident_id] = []
        self._incident_facts[fact.incident_id].append(fact)

    def get_incident_facts(self, incident_id: str) -> list[ExtractedFact]:
        """Get all registered facts for an incident."""
        return self._incident_facts.get(incident_id, [])

    async def check_contradictions(
        self, new_fact: ExtractedFact, timeout_ms: int = 0
    ) -> list[ContradictionReport]:
        """
        Check a new fact against all existing facts from OTHER callers
        in the same incident.

        Only compares across callers — facts from the same caller are
        assumed to be internally consistent (or handled by NLI).
        """
        if timeout_ms <= 0:
            timeout_ms = settings.VERIFYLAYER_LATENCY_BUDGET_MS
        existing = self._incident_facts.get(new_fact.incident_id, [])

        # Only compare against facts from OTHER callers
        cross_caller_facts = [
            f for f in existing
            if f.caller_id != new_fact.caller_id
        ]

        if not cross_caller_facts:
            return []

        # Run contradiction checks concurrently
        tasks = [
            self._check_pair(new_fact, existing_fact, timeout_ms)
            for existing_fact in cross_caller_facts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        contradictions = []
        for result in results:
            if isinstance(result, ContradictionReport):
                contradictions.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Contradiction check error: {result}")

        if contradictions:
            logger.warning(
                f"Found {len(contradictions)} contradiction(s) for fact "
                f"{new_fact.fact_id} in incident {new_fact.incident_id}"
            )

        return contradictions

    async def _check_pair(
        self,
        fact_a: ExtractedFact,
        fact_b: ExtractedFact,
        timeout_ms: int,
    ) -> Optional[ContradictionReport]:
        """Check a single pair of facts for contradiction."""
        # Quick domain pre-filter: only compare facts in overlapping domains
        if fact_a.domain != "general" and fact_b.domain != "general":
            if fact_a.domain != fact_b.domain:
                return None

        prompt = (
            f"FACT A (from {fact_a.caller_role} caller): \"{fact_a.fact_text}\"\n"
            f"FACT B (from {fact_b.caller_role} caller): \"{fact_b.fact_text}\"\n\n"
            f"Are these contradictory?"
        )

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=CONTRADICTION_MODEL,
                    contents=prompt,
                    config={
                        "system_instruction": CONTRADICTION_PROMPT,
                        "response_mime_type": "application/json",
                        "temperature": 0.0,
                        "max_output_tokens": 256,
                    },
                ),
                timeout=timeout_ms / 1000.0,
            )

            data = json.loads(response.text)

            if data.get("is_contradiction", False):
                return ContradictionReport(
                    fact_a_id=fact_a.fact_id,
                    fact_b_id=fact_b.fact_id,
                    fact_a_text=fact_a.fact_text,
                    fact_b_text=fact_b.fact_text,
                    caller_a=fact_a.caller_id,
                    caller_b=fact_b.caller_id,
                    severity=data.get("severity", 0.5),
                    contradiction_type=data.get("contradiction_type", "direct"),
                    explanation=data.get("explanation", ""),
                )

            return None

        except asyncio.TimeoutError:
            logger.debug(
                f"Contradiction check timed out: "
                f"{fact_a.fact_id} vs {fact_b.fact_id}"
            )
            return None

        except Exception as e:
            logger.error(f"Contradiction check failed: {e}")
            return None

    def clear_incident(self, incident_id: str):
        """Clear stored facts for a resolved incident."""
        self._incident_facts.pop(incident_id, None)
