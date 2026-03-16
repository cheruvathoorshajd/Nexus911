"""
Simulation Orchestrator — Runs multi-caller scenarios end-to-end.

Launches staggered simulated callers that connect to Nexus911 through the
real voice pipeline. Falls back to text-based simulation if voice fails.

Usage:
    POST /api/simulation/start {"scenario": "highway_accident", "mode": "voice"}
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from simulation.scenarios import get_scenario, list_scenarios
from simulation.simulator_agent import CallerSimSession

logger = logging.getLogger("nexus911.simulation")


@dataclass
class SimulationResult:
    """Result of a completed simulation run."""
    simulation_id: str
    scenario_name: str
    status: str  # completed, failed, partial
    mode: str  # voice, text
    total_duration: float = 0.0
    callers_completed: int = 0
    callers_failed: int = 0
    caller_results: list = field(default_factory=list)
    events: list = field(default_factory=list)
    incident_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "simulation_id": self.simulation_id,
            "scenario_name": self.scenario_name,
            "status": self.status,
            "mode": self.mode,
            "total_duration": round(self.total_duration, 2),
            "callers_completed": self.callers_completed,
            "callers_failed": self.callers_failed,
            "caller_results": self.caller_results,
            "incident_id": self.incident_id,
        }


class SimulationOrchestrator:
    """
    Manages a single scenario simulation lifecycle.

    Launches N simulated callers with staggered delays, monitors their
    progress, and reports events to connected dashboard clients.
    """

    def __init__(
        self,
        scenario_name: str,
        mode: str = "voice",
        base_url: str = "ws://localhost:8080",
        delay_multiplier: float = 1.0,
        timeout_seconds: float = 180.0,
    ):
        self.simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
        self.scenario_name = scenario_name
        self.mode = mode
        self.base_url = base_url
        self.delay_multiplier = delay_multiplier
        self.timeout_seconds = timeout_seconds

        self.scenario = get_scenario(scenario_name)
        if not self.scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        self.status = "pending"
        self.caller_sessions: dict[str, CallerSimSession] = {}
        self.events: list = []
        self._event_listeners: list = []
        self._tasks: list = []
        self.start_time: float = 0.0
        self.incident_id: Optional[str] = None

    def add_event_listener(self, callback):
        """Add a callback that receives simulation events."""
        self._event_listeners.append(callback)

    def _emit(self, event: dict):
        """Emit an event to all listeners."""
        event["simulation_id"] = self.simulation_id
        self.events.append(event)
        for listener in self._event_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    asyncio.create_task(listener(event))
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

    async def run(self) -> SimulationResult:
        """
        Execute the full scenario simulation.

        Launches all callers with staggered delays, waits for all to complete
        or timeout, then returns results.
        """
        self.start_time = time.time()
        self.status = "running"

        self._emit({
            "type": "simulation_started",
            "scenario": self.scenario_name,
            "title": self.scenario["name"],
            "caller_count": len(self.scenario["callers"]),
            "mode": self.mode,
            "time": time.time(),
        })

        logger.info(
            f"Starting simulation '{self.scenario_name}' "
            f"({len(self.scenario['callers'])} callers, mode={self.mode})"
        )

        # Launch callers
        if self.mode == "voice":
            result = await self._run_voice_simulation()
        else:
            result = await self._run_text_simulation()

        self.status = result.status

        self._emit({
            "type": "simulation_completed",
            "scenario": self.scenario_name,
            "status": result.status,
            "total_duration": result.total_duration,
            "callers_completed": result.callers_completed,
            "callers_failed": result.callers_failed,
            "incident_id": result.incident_id,
            "time": time.time(),
        })

        logger.info(
            f"Simulation '{self.scenario_name}' {result.status} "
            f"({result.total_duration:.1f}s, "
            f"{result.callers_completed}/{len(self.scenario['callers'])} callers)"
        )

        return result

    async def _run_voice_simulation(self) -> SimulationResult:
        """Run simulation using Gemini Live API voice-to-voice.
        
        Callers run concurrently with staggered delays. The frontend
        routes each caller's audio to a separate dialog box with
        individual mute/unmute controls, so audio only plays for
        the caller the user is listening to.
        """
        tasks = []
        sessions = []

        for caller_data in self.scenario["callers"]:
            session = CallerSimSession(
                caller_data=caller_data,
                scenario_data=self.scenario,
                base_url=self.base_url,
            )
            sessions.append(session)
            self.caller_sessions[caller_data["name"]] = session

            delay = caller_data.get("delay", 0.0) * self.delay_multiplier
            task = asyncio.create_task(
                self._launch_caller_with_delay(session, delay)
            )
            tasks.append(task)
            self._tasks = tasks

        # Wait for all callers to complete (or timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Simulation timed out after {self.timeout_seconds}s")
            for task in tasks:
                if not task.done():
                    task.cancel()

        # Collect results
        completed = sum(1 for s in sessions if s.status == "completed")
        failed = sum(1 for s in sessions if s.status == "failed")
        total_duration = time.time() - self.start_time

        # Get incident_id from first successful session
        for s in sessions:
            if s.incident_id:
                self.incident_id = s.incident_id
                break

        caller_results = [
            {
                "name": s.caller_name,
                "role": s.caller_data["role"],
                "status": s.status,
                "duration": round(s.duration, 2),
                "transcript_count": len(s.transcripts),
                "incident_id": s.incident_id,
            }
            for s in sessions
        ]

        status = "completed" if failed == 0 else ("partial" if completed > 0 else "failed")

        # If voice failed for ALL callers, try text fallback
        if status == "failed":
            logger.warning("All voice sessions failed — falling back to text simulation")
            return await self._run_text_simulation()

        return SimulationResult(
            simulation_id=self.simulation_id,
            scenario_name=self.scenario_name,
            status=status,
            mode="voice",
            total_duration=total_duration,
            callers_completed=completed,
            callers_failed=failed,
            caller_results=caller_results,
            events=self.events,
            incident_id=self.incident_id,
        )

    async def _run_text_simulation(self) -> SimulationResult:
        """
        Text-based fallback simulation.

        Uses the agent tools directly (submit_intelligence, add_caller_to_incident,
        etc.) to play through the scenario without voice. Still goes through the
        real VerifyLayer pipeline and knowledge graph.
        """
        from simulation.text_fallback import run_text_simulation

        return await run_text_simulation(
            scenario=self.scenario,
            scenario_name=self.scenario_name,
            simulation_id=self.simulation_id,
            delay_multiplier=self.delay_multiplier,
            event_callback=self._emit,
        )

    async def _launch_caller_with_delay(self, session: CallerSimSession, delay: float):
        """Wait for the stagger delay, then launch the caller session."""
        if delay > 0:
            self._emit({
                "type": "caller_waiting",
                "caller": session.caller_name,
                "delay": delay,
                "time": time.time(),
            })
            await asyncio.sleep(delay)

        try:
            await session.connect_and_converse(event_callback=self._emit)
        except Exception as e:
            logger.error(f"Caller {session.caller_name} failed: {e}")
            session.status = "failed"

    async def stop(self):
        """Stop all running caller sessions."""
        self.status = "stopped"
        for task in self._tasks:
            if not task.done():
                task.cancel()
        logger.info(f"Simulation {self.simulation_id} stopped")


# ═══ Global simulation state ═══

_active_simulation: Optional[SimulationOrchestrator] = None


async def start_simulation(
    scenario_name: str,
    mode: str = "voice",
    base_url: str = "ws://localhost:8080",
    delay_multiplier: float = 1.0,
    event_callback=None,
) -> SimulationResult:
    """Start a simulation and return results when complete."""
    global _active_simulation

    if _active_simulation and _active_simulation.status == "running":
        raise RuntimeError("A simulation is already running")

    orchestrator = SimulationOrchestrator(
        scenario_name=scenario_name,
        mode=mode,
        base_url=base_url,
        delay_multiplier=delay_multiplier,
    )
    if event_callback:
        orchestrator.add_event_listener(event_callback)

    _active_simulation = orchestrator
    try:
        return await orchestrator.run()
    finally:
        _active_simulation = None


def get_active_simulation() -> Optional[dict]:
    """Get the currently running simulation status."""
    if _active_simulation:
        return {
            "simulation_id": _active_simulation.simulation_id,
            "scenario_name": _active_simulation.scenario_name,
            "status": _active_simulation.status,
            "mode": _active_simulation.mode,
            "callers": {
                name: {
                    "status": s.status,
                    "duration": s.duration,
                }
                for name, s in _active_simulation.caller_sessions.items()
            },
        }
    return None


async def stop_simulation():
    """Stop the currently running simulation."""
    global _active_simulation
    if _active_simulation:
        await _active_simulation.stop()
        _active_simulation = None
