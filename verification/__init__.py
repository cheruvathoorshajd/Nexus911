"""
VerifyLayer — Anti-hallucination verification system for Nexus911.

Verifies caller utterances in real-time using NLI, cross-caller
contradiction detection, and confidence scoring.
"""

from verification.verifylayer import verify_layer, VerifyLayer
from verification.models import (
    VerifyUtteranceRequest,
    VerifyUtteranceResponse,
    VerificationResult,
    ExtractedFact,
    NLIResult,
    NLILabel,
    FactConfidence,
    ContradictionReport,
    CacheStats,
)

__all__ = [
    "verify_layer",
    "VerifyLayer",
    "VerifyUtteranceRequest",
    "VerifyUtteranceResponse",
    "VerificationResult",
    "ExtractedFact",
    "NLIResult",
    "NLILabel",
    "FactConfidence",
    "ContradictionReport",
    "CacheStats",
]
