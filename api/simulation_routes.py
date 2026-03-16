"""Simulation REST API endpoints."""
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from simulation.scenarios import list_scenarios, get_scenario
from simulation.orchestrator import (
    start_simulation,
    get_active_simulation,
    stop_simulation,
)

logger = logging.getLogger("nexus911.api.simulation")

router = APIRouter(prefix="/simulation", tags=["simulation"])


class StartSimulationRequest(BaseModel):
    scenario: str
    mode: str = "voice"  # "voice" or "text"
    delay_multiplier: float = 1.0
    base_url: str = "ws://localhost:8080"


@router.get("/scenarios")
async def get_scenarios():
    """List all available simulation scenarios."""
    return {"scenarios": list_scenarios()}


@router.get("/scenarios/{name}")
async def get_scenario_detail(name: str):
    """Get details for a specific scenario."""
    scenario = get_scenario(name)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    return scenario


@router.post("/start")
async def start_sim(request: StartSimulationRequest):
    """
    Start a scenario simulation.

    Mode "voice": Uses Gemini Live API for voice-to-voice simulation.
    Mode "text": Uses direct tool calls (reliable fallback).

    Both modes exercise the full Nexus911 pipeline:
    VerifyLayer, deduplication, knowledge graph, dispatch.
    """
    scenario = get_scenario(request.scenario)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{request.scenario}' not found. "
                   f"Available: {[s['name'] for s in list_scenarios()]}",
        )

    active = get_active_simulation()
    if active:
        raise HTTPException(
            status_code=409,
            detail=f"Simulation '{active['scenario_name']}' is already running. "
                   "Stop it first with POST /api/simulation/stop.",
        )

    # Run simulation in background so the endpoint returns immediately
    async def run_in_background():
        try:
            from api.main import broadcast_sim_event

            async def event_relay(event):
                await broadcast_sim_event(event)

            result = await start_simulation(
                scenario_name=request.scenario,
                mode=request.mode,
                base_url=request.base_url,
                delay_multiplier=request.delay_multiplier,
                event_callback=event_relay,
            )
            logger.info(f"Simulation completed: {result.to_dict()}")
        except Exception as e:
            logger.error(f"Simulation failed: {e}", exc_info=True)

    asyncio.create_task(run_in_background())

    return {
        "status": "started",
        "scenario": request.scenario,
        "mode": request.mode,
        "message": f"Simulation '{scenario['name']}' started with {len(scenario['callers'])} callers. "
                   "Watch the dashboard for real-time updates.",
    }


@router.get("/status")
async def get_sim_status():
    """Get the status of the current simulation."""
    active = get_active_simulation()
    if not active:
        return {"status": "idle", "message": "No simulation running"}
    return active


@router.post("/stop")
async def stop_sim():
    """Stop the currently running simulation."""
    active = get_active_simulation()
    if not active:
        return {"status": "idle", "message": "No simulation running"}
    await stop_simulation()
    return {"status": "stopped", "message": "Simulation stopped"}
