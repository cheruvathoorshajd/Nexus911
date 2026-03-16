"""Tests for the incident knowledge graph."""
import pytest
from core.incident_graph import Incident, IncidentManager, CallerInfo, CallerRole


class TestIncident:
    def test_create_incident(self):
        inc = Incident(
            incident_type="fire",
            location="123 Main St",
            summary="Building fire",
        )
        assert inc.id.startswith("inc_")
        assert inc.incident_type == "fire"

    def test_add_caller(self):
        inc = Incident(
            incident_type="fire",
            location="123 Main St",
            summary="Building fire",
        )
        caller = CallerInfo(id="caller-1", role=CallerRole.WITNESS)
        inc.add_caller(caller)
        assert "caller-1" in inc.callers

    def test_update_intel(self):
        inc = Incident(
            incident_type="fire",
            location="123 Main St",
            summary="Building fire",
        )
        caller = CallerInfo(id="caller-1")
        inc.add_caller(caller)
        inc.update_intel("caller-1", "Smoke visible from second floor")
        assert len(inc.timeline) > 0
        assert "Smoke visible" in inc.callers["caller-1"].key_intel[0]

    def test_suspect_info(self):
        inc = Incident(
            incident_type="assault",
            location="456 Oak Ave",
            summary="Assault in progress",
        )
        inc.update_suspect(description="Male, 6ft, red jacket")
        assert "red jacket" in inc.suspect.description

    def test_briefing_generation(self):
        inc = Incident(
            incident_type="fire",
            location="123 Main St",
            summary="Building fire",
        )
        caller = CallerInfo(id="caller-1")
        inc.add_caller(caller)
        inc.update_intel("caller-1", "Two people trapped")
        briefing = inc.get_briefing()
        assert "FIRE" in briefing or "123 Main St" in briefing

    def test_to_dict(self):
        inc = Incident(
            incident_type="fire",
            location="123 Main St",
            summary="Building fire",
        )
        d = inc.to_dict()
        assert d["id"].startswith("inc_")
        assert d["location"] == "123 Main St"


class TestIncidentManager:
    def test_create_and_retrieve(self):
        mgr = IncidentManager()
        inc = mgr.create_incident(
            incident_type="fire", location="Test",
            description="Test fire", caller_id="caller-1",
        )
        retrieved = mgr.get_incident(inc.id)
        assert retrieved is not None
        assert retrieved.id == inc.id

    def test_get_active(self):
        mgr = IncidentManager()
        mgr.create_incident(
            incident_type="fire", location="A",
            description="Fire at A", caller_id="caller-1",
        )
        mgr.create_incident(
            incident_type="medical", location="B",
            description="Medical at B", caller_id="caller-2",
        )
        active = mgr.get_active_incidents()
        assert len(active) >= 2
