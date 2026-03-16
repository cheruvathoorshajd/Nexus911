"""
VerifyLayer FastAPI Router — REST API endpoints for verification.

Endpoints:
    POST /verify/utterance       — Verify an utterance and extract facts
    GET  /verify/intel/{id}/{ag} — Get verified facts for an incident/agent
    GET  /verify/facts/{id}      — Get all facts for an incident
    GET  /verify/cache/stats     — Cache performance statistics
"""
import logging
from fastapi import APIRouter, HTTPException

from verification.verifylayer import verify_layer
from verification.models import (
    VerifyUtteranceRequest,
    VerifyUtteranceResponse,
    CacheStats,
)

logger = logging.getLogger("nexus911.verifylayer.api")

router = APIRouter(prefix="/verify", tags=["verifylayer"])


@router.post("/utterance", response_model=VerifyUtteranceResponse)
async def verify_utterance(request: VerifyUtteranceRequest):
    """
    Verify a caller utterance for factual accuracy.

    Extracts facts from the utterance (or uses pre-extracted facts),
    runs NLI verification, checks cross-caller contradictions,
    and scores confidence. Completes within 200ms latency budget.
    """
    try:
        response = await verify_layer.verify_utterance(
            incident_id=request.incident_id,
            caller_id=request.caller_id,
            caller_role=request.caller_role,
            agent_id=request.agent_id,
            utterance=request.utterance,
            facts=request.facts if request.facts else None,
        )
        return response

    except Exception as e:
        logger.error(f"Verification endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/intel/{incident_id}/{agent_id}")
async def get_agent_intel(incident_id: str, agent_id: str):
    """Get all verified facts for a specific agent within an incident."""
    try:
        intel = await verify_layer.get_incident_intel(
            incident_id=incident_id,
            agent_id=agent_id,
        )
        return intel

    except Exception as e:
        logger.error(f"Get agent intel error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facts/{incident_id}")
async def get_incident_facts(incident_id: str):
    """Get all verified facts for an incident across all callers."""
    try:
        intel = await verify_layer.get_incident_intel(incident_id=incident_id)
        return intel

    except Exception as e:
        logger.error(f"Get incident facts error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", response_model=CacheStats)
async def get_cache_stats():
    """Get verification cache performance statistics."""
    return await verify_layer.cache.get_stats()
