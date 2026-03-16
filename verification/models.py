"""
Pydantic models for the VerifyLayer verification system.

These models define the data structures for fact extraction,
NLI verification results, contradiction reports, and confidence scores.
"""
import hashlib
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NLILabel(str, Enum):
    """Natural Language Inference labels."""
    ENTAILMENT = "entailment"
    CONTRADICTION = "contradiction"
    NEUTRAL = "neutral"


class CallerRole(str, Enum):
    """Caller role classifications for credibility weighting."""
    VICTIM = "victim"
    WITNESS = "witness"
    BYSTANDER = "bystander"
    CHILD = "child"
    REPORTING_PARTY = "reporting_party"
    INVOLVED_PARTY = "involved_party"
    REPEAT_CALLER = "repeat_caller"
    OFFICIAL = "official"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, s: str) -> "CallerRole":
        """Convert any case role string to CallerRole enum."""
        try:
            return cls(s.lower())
        except ValueError:
            return cls.UNKNOWN


class ExtractedFact(BaseModel):
    """A single fact extracted from a caller utterance."""
    fact_id: str = ""
    incident_id: str
    caller_id: str
    caller_role: str = "unknown"
    agent_id: str = ""
    fact_text: str
    domain: str = "general"  # location, suspect, vehicle, medical, etc.
    timestamp: float = 0.0

    def model_post_init(self, __context):
        if not self.fact_id:
            content = f"{self.incident_id}:{self.fact_text.lower().strip()}"
            self.fact_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        if not self.timestamp:
            import time
            self.timestamp = time.time()


class NLIResult(BaseModel):
    """Result of NLI verification for a single fact."""
    label: NLILabel = NLILabel.NEUTRAL
    score: float = 0.0  # Confidence in the label (0-1)
    premise: str = ""  # What we verified against
    hypothesis: str = ""  # The fact being verified


class ContradictionReport(BaseModel):
    """Report of a contradiction between two facts."""
    fact_a_id: str
    fact_b_id: str
    fact_a_text: str
    fact_b_text: str
    caller_a: str
    caller_b: str
    severity: float = 0.5  # 0-1
    contradiction_type: str = "direct"
    explanation: str = ""


class FactConfidence(BaseModel):
    """Composite confidence score for a verified fact."""
    nli_score: float = 0.0
    caller_credibility: float = 0.5
    cross_caller_agreement: float = 0.0
    contradiction_penalty: float = 0.0
    overall: float = 0.0


class VerificationResult(BaseModel):
    """Complete verification result for a single fact."""
    fact: ExtractedFact
    nli: NLIResult = Field(default_factory=NLIResult)
    confidence: FactConfidence = Field(default_factory=FactConfidence)
    contradictions: list[ContradictionReport] = Field(default_factory=list)
    from_cache: bool = False


class VerifyUtteranceRequest(BaseModel):
    """Request to verify a caller utterance."""
    incident_id: str
    caller_id: str
    caller_role: str = "unknown"
    agent_id: str = ""
    utterance: str
    facts: Optional[list[str]] = None  # Pre-extracted facts, or None to auto-extract


class VerifyUtteranceResponse(BaseModel):
    """Response from utterance verification."""
    incident_id: str
    caller_id: str
    results: list[VerificationResult] = Field(default_factory=list)
    latency_ms: float = 0.0


class CacheStats(BaseModel):
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 1024
    hit_rate: float = 0.0
    evictions: int = 0
