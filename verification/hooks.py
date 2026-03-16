"""
Integration Hooks — Connect VerifyLayer to existing voice agent pipeline.

These hooks intercept the transcript/intel flow in the voice session
manager and incident tools, routing facts through verification before
they enter the Incident Knowledge Graph.

Designed as non-blocking wrappers: if verification fails or times out,
the original data flows through unverified (fail-open for 911 safety).
"""
import logging
import asyncio
from typing import Optional

from core.incident_graph import incident_manager
from verification.verifylayer import verify_layer
from verification.models import VerifyUtteranceResponse, NLILabel

logger = logging.getLogger("nexus911.verifylayer.hooks")


async def verify_before_intel_submit(
    incident_id: str,
    caller_id: str,
    caller_role: str,
    agent_id: str,
    intel: str,
    utterance: str = "",
) -> dict:
    """
    Hook to verify intelligence before it enters the knowledge graph.

    Call this BEFORE incident.update_intel() to get verification metadata.
    The intel still enters the graph regardless (fail-open for safety),
    but verification metadata is attached.

    Args:
        incident_id: The incident ID.
        caller_id: Caller providing the intel.
        caller_role: VICTIM, WITNESS, etc.
        agent_id: The handling agent.
        intel: The intelligence/fact being submitted.
        utterance: Raw transcript (if available, improves NLI accuracy).

    Returns:
        dict with verification results and the original intel.
    """
    # Use the intel itself as both fact and utterance if no utterance provided
    source_text = utterance if utterance else intel

    try:
        response = await verify_layer.verify_utterance(
            incident_id=incident_id,
            caller_id=caller_id,
            caller_role=caller_role,
            agent_id=agent_id,
            utterance=source_text,
            facts=[intel],
        )

        # Extract key metrics for the knowledge graph
        if response.results:
            result = response.results[0]
            # Build contradiction explanation string for dashboard
            contra_details = ""
            if result.contradictions:
                explanations = [c.explanation for c in result.contradictions if c.explanation]
                if explanations:
                    contra_details = "; ".join(explanations)
            verification_meta = {
                "verified": result.nli.label == NLILabel.ENTAILMENT,
                "nli_label": result.nli.label.value,
                "confidence": result.confidence.overall,
                "contradictions": len(result.contradictions),
                "contradiction_details": contra_details,
                "from_cache": result.from_cache,
                "latency_ms": response.latency_ms,
            }
        else:
            verification_meta = {
                "verified": False,
                "nli_label": "pending",
                "confidence": 0.0,
                "contradictions": 0,
                "from_cache": False,
                "latency_ms": response.latency_ms,
            }

        logger.info(
            f"Verification hook: {intel[:50]}... → "
            f"{verification_meta['nli_label']} "
            f"(confidence={verification_meta['confidence']:.2f})"
        )

        return {
            "intel": intel,
            "verification": verification_meta,
            "pass_through": True,  # Always allow intel through (fail-open)
        }

    except Exception as e:
        logger.error(f"Verification hook failed (fail-open): {e}")
        return {
            "intel": intel,
            "verification": {
                "verified": False,
                "nli_label": "error",
                "confidence": 0.0,
                "error": str(e),
            },
            "pass_through": True,
        }


async def verify_transcript_chunk(
    incident_id: str,
    caller_id: str,
    caller_role: str,
    agent_id: str,
    transcript_text: str,
) -> VerifyUtteranceResponse:
    """
    Hook for verifying streaming transcript chunks.

    Called from the voice WebSocket handler when a new transcript
    chunk arrives. Extracts and verifies all facts in the chunk.

    Non-blocking: fires verification in background, returns immediately
    if called with asyncio.create_task().
    """
    return await verify_layer.verify_utterance(
        incident_id=incident_id,
        caller_id=caller_id,
        caller_role=caller_role,
        agent_id=agent_id,
        utterance=transcript_text,
    )


def attach_verification_to_incident(
    incident_id: str,
    caller_id: str,
    intel: str,
    verification_meta: dict,
):
    """
    Attach verification metadata to an intel entry in the knowledge graph.

    Enriches the timeline entry with confidence and contradiction data.
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return

    # Add verification flag to the intel string for dashboard display
    confidence = verification_meta.get("confidence", 0.0)
    nli_label = verification_meta.get("nli_label", "pending")

    if nli_label == "entailment" and confidence > 0.7:
        verified_intel = f"[VERIFIED ✓ {confidence:.0%}] {intel}"
    elif nli_label == "contradiction":
        # Include explanation from contradiction reports if available
        contra_details = verification_meta.get("contradiction_details", "")
        verified_intel = f"[CONTRADICTED ✗] {intel}"
        if contra_details:
            verified_intel = f"[CONTRADICTED ✗ — {contra_details}] {intel}"
    elif nli_label == "pending" or nli_label == "pending_verification":
        verified_intel = f"[PENDING ⏳] {intel}"
    else:
        verified_intel = f"[UNVERIFIED {confidence:.0%}] {intel}"

    # Update the most recent timeline entry for this intel
    for entry in reversed(incident.timeline):
        if entry.get("source") == caller_id and intel in entry.get("event", ""):
            entry["event"] = verified_intel
            entry["verification"] = verification_meta
            break

    incident.updated_at = __import__("time").time()
