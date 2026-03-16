"""
Caller Simulator — Runs multi-caller emergency scenarios through the real Nexus911 pipeline.

Demonstrates the full system end-to-end:
  1. Multiple callers report the same incident
  2. Each caller gets a role-specific agent
  3. Intel is submitted and verified via VerifyLayer
  4. Incidents are deduplicated
  5. Cross-call contradictions are detected
  6. A dispatch package is produced

Usage:
    python -m simulation.caller_simulator
    python -m simulation.caller_simulator --scenario highway_accident
    python -m simulation.caller_simulator --scenario domestic_violence_with_children
"""
import asyncio
import time
import sys
import argparse
import logging

from core.incident_graph import incident_manager
from agents.tools.incident_tools import (
    report_new_emergency,
    add_caller_to_incident,
    submit_intelligence,
    update_suspect_info,
    dispatch_units,
)
from agents.tools.dispatch_tools import recommend_response_units
from simulation.scenarios import SCENARIOS

logger = logging.getLogger("nexus911.simulator")

# ─── ANSI Colors ─────────────────────────────────────────────
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

ROLE_COLORS = {
    "VICTIM": RED,
    "WITNESS": BLUE,
    "BYSTANDER": CYAN,
    "CHILD": YELLOW,
    "REPORTING_PARTY": MAGENTA,
    "OFFICIAL": GREEN,
    "UNKNOWN": WHITE,
}


def _ts(start: float) -> str:
    """Elapsed time since start as formatted string."""
    elapsed = time.time() - start
    return f"{DIM}T+{elapsed:05.1f}s{RESET}"


def _role_tag(role: str) -> str:
    color = ROLE_COLORS.get(role, WHITE)
    return f"{color}{BOLD}[{role}]{RESET}"


def _section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {BOLD}{title}{RESET}")
    print(f"{'─' * 60}")


# ─── Built-in Scenarios ─────────────────────────────────────

BUILTIN_SCENARIOS = {
    "highway_accident": {
        "name": "Highway Multi-Vehicle Accident",
        "incident_type": "vehicle_accident",
        "severity": "CRITICAL",
        "location": "Route 9 and Elm Street",
        "latitude": 40.7580,
        "longitude": -73.9855,
        "callers": [
            {
                "name": "Tommy (child, age 8)",
                "role": "CHILD",
                "location": "Backseat of blue Camry",
                "intel": [
                    "We crashed and mommy isn't moving",
                    "There's a big truck next to us",
                    "My sister is crying but she's okay",
                    "The car is making funny noises",
                ],
                "delay": 0.0,
            },
            {
                "name": "David Chen (witness)",
                "role": "WITNESS",
                "location": "Sidewalk across from Route 9 and Elm",
                "intel": [
                    "A sedan just hit an 18-wheeler at Route 9 and Elm",
                    "The sedan is a blue Camry, looks badly damaged on the driver side",
                    "I can see two people in the sedan, driver appears unconscious",
                    "The truck driver is out of his cab, he looks okay",
                    "Traffic is backing up in both directions",
                ],
                "delay": 3.0,
            },
            {
                "name": "Maria Santos (victim, truck driver)",
                "role": "VICTIM",
                "location": "Cab of 18-wheeler at Route 9 and Elm",
                "intel": [
                    "I was in my truck and a blue car ran the red light and hit me",
                    "I'm okay but shaken up, my truck has minor damage",
                    "The car driver is not responding, I tried to check on them",
                    "There are kids in the backseat of the car, they're crying",
                ],
                "delay": 6.0,
            },
        ],
    },
}

# Merge built-in scenarios with scenarios.py
ALL_SCENARIOS = {**BUILTIN_SCENARIOS, **SCENARIOS}


async def run_scenario(scenario_name: str):
    """Run a full multi-caller scenario through the Nexus911 pipeline."""
    scenario = ALL_SCENARIOS.get(scenario_name)
    if not scenario:
        print(f"{RED}Unknown scenario: {scenario_name}{RESET}")
        print(f"Available: {', '.join(ALL_SCENARIOS.keys())}")
        return

    start = time.time()
    callers = scenario["callers"]
    location = scenario.get("location", "Unknown location")
    latitude = scenario.get("latitude", 0.0)
    longitude = scenario.get("longitude", 0.0)

    _section(f"NEXUS911 SIMULATION: {scenario['name']}")
    print(f"  {DIM}Started:  {time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"  {DIM}Location: {location}{RESET}")
    print(f"  {DIM}Callers:  {len(callers)}{RESET}")
    print(f"  {DIM}Severity: {scenario.get('severity', 'UNKNOWN')}{RESET}")
    print()

    incident_id = None
    caller_ids = {}
    results_by_caller = {}

    # ─── Phase 1: Callers report in ─────────────────────────
    _section("PHASE 1 — INCOMING CALLS")

    for i, caller in enumerate(callers):
        delay = caller.get("delay", i * 3.0)
        if delay > 0:
            await asyncio.sleep(min(delay, 1.0))  # Simulated delay (capped for demo)

        role = caller["role"]
        name = caller["name"]
        caller_location = caller.get("location", location)

        # First intel as description
        description = caller.get("opening", caller.get("intel", ["Emergency"])[0])

        print(f"  {_ts(start)}  {_role_tag(role)}  ☎ {BOLD}{name}{RESET} calls 911")
        print(f"           {DIM}\"{description}\"{RESET}")

        # First caller creates the incident; subsequent callers use the same
        # incident-level location so deduplication can match them.
        report_location = location  # Use the shared incident location for dedup
        result = report_new_emergency(
            location=report_location,
            description=description,
            latitude=latitude,
            longitude=longitude,
        )

        if incident_id is None:
            incident_id = result["incident_id"]
            print(f"  {_ts(start)}  {GREEN}✓ New incident created: {incident_id}{RESET}")
        else:
            if result.get("status") == "deduplicated":
                conf = result.get("dedup_confidence", 0)
                print(f"  {_ts(start)}  {CYAN}⟳ Deduplicated into {incident_id} {BOLD}(match: {conf:.0%}){RESET}")
            else:
                # If dedup didn't fire (different location text), use same incident
                incident_id = result.get("incident_id", incident_id)

        # Register caller
        caller_result = add_caller_to_incident(
            incident_id=incident_id,
            caller_name=name,
            caller_role=role,
            caller_location=caller_location,
        )
        cid = caller_result.get("caller_id", f"caller_{i}")
        caller_ids[name] = cid
        results_by_caller[name] = {"role": role, "intel": [], "caller_id": cid}

        print(f"  {_ts(start)}  {DIM}  └─ Caller registered: {cid} ({role}){RESET}")

    # ─── Phase 2: Intel submission with verification ────────
    _section("PHASE 2 — INTELLIGENCE GATHERING + VERIFICATION")

    for caller in callers:
        name = caller["name"]
        role = caller["role"]
        cid = caller_ids[name]
        intel_items = caller.get("intel", [])

        for intel in intel_items:
            await asyncio.sleep(0.3)  # Simulate conversation pace

            print(f"  {_ts(start)}  {_role_tag(role)}  📋 {name}: \"{intel}\"")

            result = submit_intelligence(
                incident_id=incident_id,
                caller_id=cid,
                intel=intel,
                caller_role=role,
                agent_id=f"agent_{role.lower()}",
            )

            results_by_caller[name]["intel"].append(intel)

            if result.get("status") == "intel_recorded":
                print(f"  {_ts(start)}  {GREEN}  └─ ✓ Intel recorded & queued for verification{RESET}")
            else:
                print(f"  {_ts(start)}  {RED}  └─ ✗ {result.get('message', 'Error')}{RESET}")

    # Small pause for async verification tasks to complete
    await asyncio.sleep(1.0)

    # ─── Phase 3: Check for contradictions & suspect info ───
    _section("PHASE 3 — CROSS-CALLER ANALYSIS")

    # Check incident briefing
    incident = incident_manager.get_incident(incident_id)
    if incident:
        # Look for verification markers in timeline
        verified_count = 0
        contradicted_count = 0
        pending_count = 0

        for entry in incident.timeline:
            event_text = entry.get("event", "")
            verification = entry.get("verification", {})
            if "[VERIFIED" in event_text:
                verified_count += 1
            elif "[CONTRADICTED" in event_text:
                contradicted_count += 1
                print(f"  {_ts(start)}  {RED}⚠ CONTRADICTION: {event_text[:80]}...{RESET}")
            elif "[PENDING" in event_text:
                pending_count += 1

        print(f"  {_ts(start)}  {GREEN}Verified facts: {verified_count}{RESET}")
        if contradicted_count:
            print(f"  {_ts(start)}  {RED}Contradictions: {contradicted_count}{RESET}")
        if pending_count:
            print(f"  {_ts(start)}  {YELLOW}Pending verification: {pending_count}{RESET}")

    # ─── Phase 4: Dispatch recommendation ───────────────────
    _section("PHASE 4 — DISPATCH")

    incident_type = scenario.get("incident_type", "emergency")
    severity = scenario.get("severity", "HIGH")
    armed = incident.suspect.armed if incident and incident.suspect else False

    rec = recommend_response_units(
        incident_type=incident_type,
        severity=severity,
        armed_suspect=armed,
        children_involved=any(c.get("role") == "CHILD" for c in callers),
        victims_count=sum(1 for c in callers if c.get("role") == "VICTIM"),
    )

    print(f"  {_ts(start)}  {BOLD}Recommended units:{RESET}")
    for unit in rec.get("recommended_units", []):
        print(f"           {GREEN}▸ {unit}{RESET}")

    # Dispatch
    dispatch_result = dispatch_units(
        incident_id=incident_id,
        units=rec.get("recommended_units", ["Patrol Unit"]),
    )
    print(f"  {_ts(start)}  {GREEN}✓ Units dispatched{RESET}")

    # ─── Phase 5: Final briefing ────────────────────────────
    _section("FINAL DISPATCH PACKAGE")

    if incident:
        briefing = incident.get_briefing()
        for line in briefing.split("\n"):
            color = GREEN if "VERIFIED" in line else (RED if "CONTRADICTED" in line else WHITE)
            print(f"  {color}{line}{RESET}")

    # Summary
    elapsed = time.time() - start
    _section("SIMULATION COMPLETE")
    print(f"  {BOLD}Total time:     {elapsed:.1f}s{RESET}")
    print(f"  {BOLD}Callers:        {len(callers)}{RESET}")
    print(f"  {BOLD}Incident ID:    {incident_id}{RESET}")
    print(f"  {BOLD}Intel items:    {sum(len(c.get('intel', [])) for c in callers)}{RESET}")
    if incident:
        print(f"  {BOLD}Timeline items: {len(incident.timeline)}{RESET}")
        print(f"  {BOLD}Units sent:     {', '.join(incident.dispatched_units)}{RESET}")
        if incident.dedup_confidence > 0:
            conf_color = GREEN if incident.dedup_confidence >= 0.8 else (YELLOW if incident.dedup_confidence >= 0.5 else RED)
            print(f"  {BOLD}Dedup match:    {conf_color}{incident.dedup_confidence:.0%}{RESET} ({incident.merged_caller_count} callers merged)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Nexus911 Multi-Caller Simulator")
    parser.add_argument(
        "--scenario", "-s",
        default="highway_accident",
        help=f"Scenario to run (available: {', '.join(ALL_SCENARIOS.keys())})",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available scenarios",
    )
    args = parser.parse_args()

    if args.list:
        print(f"\n{BOLD}Available Scenarios:{RESET}\n")
        for name, scenario in ALL_SCENARIOS.items():
            s_name = scenario.get("name", name)
            n_callers = len(scenario.get("callers", []))
            print(f"  {GREEN}▸{RESET} {name}")
            print(f"    {DIM}{s_name} — {n_callers} callers{RESET}")
        print()
        return

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    # Silence VerifyLayer background errors during simulation — they're non-fatal
    # and would flood the terminal output with API quota/timeout messages
    logging.getLogger("nexus911.verifylayer").setLevel(logging.CRITICAL)
    logging.getLogger("nexus911.tools").setLevel(logging.CRITICAL)

    asyncio.run(run_scenario(args.scenario))


if __name__ == "__main__":
    main()
