"""
Text-based simulation fallback.

When Gemini Live API voice sessions fail, this module provides a reliable
fallback that still exercises the full Nexus911 pipeline:
  - Incident creation and deduplication
  - Caller registration with roles
  - Intelligence submission through VerifyLayer
  - Cross-caller contradiction detection
  - Suspect info updates and severity escalation
  - Unit recommendation and dispatch

The dashboard shows everything in real-time, just without audio.
"""
import asyncio
import logging
import time

logger = logging.getLogger("nexus911.simulation.text")


async def run_text_simulation(
    scenario: dict,
    scenario_name: str,
    simulation_id: str,
    delay_multiplier: float = 1.0,
    event_callback=None,
):
    """
    Play through a scenario using direct tool calls.

    Each caller's intel is submitted piece-by-piece through the real
    VerifyLayer pipeline, with realistic delays between callers.
    """
    from agents.tools.incident_tools import (
        report_new_emergency,
        add_caller_to_incident,
        submit_intelligence,
        update_suspect_info,
        dispatch_units,
    )
    from agents.tools.dispatch_tools import recommend_response_units
    from simulation.orchestrator import SimulationResult

    start_time = time.time()
    incident_id = None
    callers_completed = 0
    caller_results = []
    events = []

    def emit(event_type: str, data: dict):
        event = {"type": event_type, "simulation_id": simulation_id, "time": time.time(), **data}
        events.append(event)
        if event_callback:
            try:
                if asyncio.iscoroutinefunction(event_callback):
                    asyncio.create_task(event_callback(event))
                else:
                    event_callback(event)
            except Exception:
                pass

    emit("simulation_started", {
        "scenario": scenario_name,
        "title": scenario["name"],
        "mode": "text",
        "caller_count": len(scenario["callers"]),
    })

    for i, caller_data in enumerate(scenario["callers"]):
        caller_name = caller_data["name"]
        caller_role = caller_data["role"]
        delay = caller_data.get("delay", 0.0) * delay_multiplier
        caller_start = time.time()

        # Stagger delay
        if delay > 0:
            emit("caller_waiting", {"caller": caller_name, "delay": delay})
            await asyncio.sleep(delay)

        emit("caller_connecting", {"caller": caller_name, "role": caller_role})

        try:
            # First caller creates the incident
            if i == 0:
                result = report_new_emergency(
                    location=scenario["location"],
                    description=caller_data.get("opening", scenario["name"]),
                    latitude=scenario.get("latitude", 0.0),
                    longitude=scenario.get("longitude", 0.0),
                    incident_type=scenario.get("incident_type", "emergency"),
                )
                incident_id = result["incident_id"]
                logger.info(f"[TEXT] Incident created: {incident_id}")
            else:
                # Subsequent callers — dedup will merge into existing incident
                result = report_new_emergency(
                    location=scenario["location"],
                    description=caller_data.get("opening", ""),
                    latitude=scenario.get("latitude", 0.0),
                    longitude=scenario.get("longitude", 0.0),
                    incident_type=scenario.get("incident_type", "emergency"),
                )
                merged_id = result["incident_id"]
                if merged_id == incident_id:
                    logger.info(f"[TEXT] Caller {caller_name} deduplicated into {incident_id}")
                    emit("dedup_merged", {
                        "caller": caller_name,
                        "incident_id": incident_id,
                        "confidence": result.get("dedup_confidence", 0),
                    })

            # Register caller
            caller_result = add_caller_to_incident(
                incident_id=incident_id,
                caller_name=caller_name,
                caller_role=caller_role,
                caller_location=caller_data.get("location", ""),
            )
            caller_id = caller_result.get("caller_id", f"caller_{i}")

            emit("caller_connected", {
                "caller": caller_name,
                "caller_id": caller_id,
                "incident_id": incident_id,
                "role": caller_role,
            })

            # Submit opening statement
            emit("transcript", {
                "caller": caller_name,
                "speaker": "caller",
                "text": caller_data.get("opening", ""),
            })

            # Submit each piece of intel with small delays (simulates conversation)
            for intel in caller_data.get("intel", []):
                await asyncio.sleep(0.8 * delay_multiplier)  # Conversation pacing

                submit_intelligence(
                    incident_id=incident_id,
                    caller_id=caller_id,
                    intel=intel,
                    caller_role=caller_role,
                    agent_id=f"sim_agent_{caller_role.lower()}",
                    utterance=intel,
                )

                emit("transcript", {
                    "caller": caller_name,
                    "speaker": "caller",
                    "text": intel,
                })
                emit("intel_submitted", {
                    "caller": caller_name,
                    "intel": intel,
                })

            # Handle suspect info for domestic violence / active shooter scenarios
            if scenario.get("incident_type") in ("domestic_violence", "active_shooter"):
                _submit_suspect_info(incident_id, caller_data, scenario)

            caller_duration = time.time() - caller_start
            caller_results.append({
                "name": caller_name,
                "role": caller_role,
                "status": "completed",
                "duration": round(caller_duration, 2),
                "intel_count": len(caller_data.get("intel", [])),
            })
            callers_completed += 1

            emit("caller_completed", {
                "caller": caller_name,
                "duration": caller_duration,
                "status": "completed",
            })

        except Exception as e:
            logger.error(f"[TEXT] Caller {caller_name} failed: {e}")
            caller_results.append({
                "name": caller_name,
                "role": caller_role,
                "status": "failed",
                "error": str(e),
            })
            emit("caller_error", {"caller": caller_name, "error": str(e)})

    # After all callers: recommend and dispatch units
    if incident_id:
        await asyncio.sleep(0.5)
        try:
            from core.incident_graph import incident_manager
            incident = incident_manager.get_incident(incident_id)

            rec = recommend_response_units(
                incident_type=scenario.get("incident_type", "emergency"),
                severity=scenario.get("severity", "HIGH"),
                armed_suspect=incident.suspect.armed if incident else False,
                children_involved=incident.children_involved if incident else False,
                victims_count=incident.victims_count if incident else 0,
            )
            units = rec.get("recommended_units", ["Patrol Unit", "EMS"])

            dispatch_units(incident_id=incident_id, units=units)

            emit("units_dispatched", {
                "incident_id": incident_id,
                "units": units,
            })
        except Exception as e:
            logger.error(f"[TEXT] Dispatch failed: {e}")

    total_duration = time.time() - start_time

    emit("simulation_completed", {
        "scenario": scenario_name,
        "status": "completed",
        "total_duration": total_duration,
        "callers_completed": callers_completed,
        "incident_id": incident_id,
    })

    return SimulationResult(
        simulation_id=simulation_id,
        scenario_name=scenario_name,
        status="completed",
        mode="text",
        total_duration=total_duration,
        callers_completed=callers_completed,
        callers_failed=len(scenario["callers"]) - callers_completed,
        caller_results=caller_results,
        events=events,
        incident_id=incident_id,
    )


def _submit_suspect_info(incident_id: str, caller_data: dict, scenario: dict):
    """Extract and submit suspect info from caller intel."""
    from agents.tools.incident_tools import update_suspect_info

    role = caller_data["role"]
    intel_text = " ".join(caller_data.get("intel", []))
    lower = intel_text.lower()

    # Detect weapon mentions
    armed = False
    weapon_type = ""

    weapon_keywords = {
        "knife": "knife",
        "kitchen knife": "kitchen knife",
        "baseball bat": "baseball bat",
        "gun": "firearm",
        "firearm": "firearm",
        "rifle": "rifle",
        "pistol": "pistol",
        "weapon": "unknown weapon",
    }

    for keyword, weapon in weapon_keywords.items():
        if keyword in lower:
            armed = True
            weapon_type = weapon
            break

    if armed or "suspect" in lower or "threatening" in lower:
        update_suspect_info(
            incident_id=incident_id,
            armed=armed,
            weapon_type=weapon_type,
            description=f"Reported by {caller_data['name']} ({role})",
        )
