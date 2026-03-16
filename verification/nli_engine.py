"""
NLI Engine — Natural Language Inference using Gemini 2.0 Flash.

Determines if a caller's statement (hypothesis) is ENTAILED by,
CONTRADICTS, or is NEUTRAL to known facts (premise).

Uses structured JSON output for reliable parsing.
"""
import json
import logging
import asyncio
from typing import Optional

from google import genai

from core.config import settings
from verification.models import NLIResult, NLILabel

logger = logging.getLogger("nexus911.verifylayer.nli")

NLI_MODEL = "gemini-2.5-flash"

NLI_SYSTEM_PROMPT = """You are a Natural Language Inference (NLI) engine for a 911 emergency system.

Given a PREMISE (known verified information) and a HYPOTHESIS (new caller statement),
determine the relationship:

- ENTAILED: The hypothesis is supported by the premise
- CONTRADICTION: The hypothesis conflicts with the premise  
- NEUTRAL: The hypothesis is unrelated or cannot be determined from the premise

For emergency contexts, be conservative:
- If a fact is plausible but not directly verified, return NEUTRAL (not contradiction)
- Only return CONTRADICTION for clear factual conflicts
- Return ENTAILED only when the premise clearly supports the hypothesis

Respond ONLY with JSON:
{
    "label": "entailment" | "contradiction" | "neutral",
    "score": 0.0 to 1.0,
    "reasoning": "Brief explanation"
}"""


class NLIEngine:
    """Gemini-based NLI engine for fact verification."""

    def __init__(self, api_key: str = ""):
        from core.config import create_genai_client
        self._client = create_genai_client()

    async def verify(
        self,
        premise: str,
        hypothesis: str,
        timeout_ms: int = 0,
    ) -> NLIResult:
        """
        Run NLI verification: does the premise entail/contradict the hypothesis?

        Args:
            premise: Known verified information.
            hypothesis: New statement to verify.
            timeout_ms: Timeout in milliseconds (0 = use config default).

        Returns:
            NLIResult with label, score, premise, and hypothesis.
        """
        if timeout_ms <= 0:
            timeout_ms = settings.VERIFYLAYER_LATENCY_BUDGET_MS

        if not premise or not hypothesis:
            return NLIResult(
                label=NLILabel.NEUTRAL,
                score=0.0,
                premise=premise,
                hypothesis=hypothesis,
            )

        prompt = f"PREMISE: \"{premise}\"\nHYPOTHESIS: \"{hypothesis}\""

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=NLI_MODEL,
                    contents=prompt,
                    config={
                        "system_instruction": NLI_SYSTEM_PROMPT,
                        "response_mime_type": "application/json",
                        "temperature": 0.0,
                        "max_output_tokens": 256,
                    },
                ),
                timeout=timeout_ms / 1000.0,
            )

            data = json.loads(response.text)

            label_str = data.get("label", "neutral").lower()
            try:
                label = NLILabel(label_str)
            except ValueError:
                label = NLILabel.NEUTRAL

            return NLIResult(
                label=label,
                score=float(data.get("score", 0.0)),
                premise=premise,
                hypothesis=hypothesis,
            )

        except asyncio.TimeoutError:
            logger.warning(f"NLI verification timed out ({timeout_ms}ms)")
            return NLIResult(
                label=NLILabel.NEUTRAL,
                score=0.0,
                premise=premise,
                hypothesis=hypothesis,
            )

        except Exception as e:
            logger.error(f"NLI verification failed: {e}")
            return NLIResult(
                label=NLILabel.NEUTRAL,
                score=0.0,
                premise=premise,
                hypothesis=hypothesis,
            )

    async def extract_facts(
        self,
        utterance: str,
        timeout_ms: int = 0,
    ) -> list[str]:
        """
        Extract verifiable facts from a caller utterance.

        Returns a list of discrete factual claims that can be individually
        verified. Filters out opinions, emotions, and requests.
        """
        if timeout_ms <= 0:
            timeout_ms = settings.VERIFYLAYER_LATENCY_BUDGET_MS
        prompt = f"""Extract discrete verifiable facts from this 911 caller statement.
Return ONLY a JSON array of fact strings. Exclude opinions, emotions, and questions.

STATEMENT: "{utterance}"

Example output: ["There is a red car on Main St", "Two people are injured"]"""

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=NLI_MODEL,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.0,
                        "max_output_tokens": 512,
                    },
                ),
                timeout=timeout_ms / 1000.0,
            )

            facts = json.loads(response.text)
            if isinstance(facts, list):
                return [str(f) for f in facts if f]
            return []

        except asyncio.TimeoutError:
            logger.warning("Fact extraction timed out")
            return [utterance]  # Fall back to treating entire utterance as one fact

        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return [utterance]
