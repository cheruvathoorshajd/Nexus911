"""Tests for the incident knowledge graph."""
import pytest
from core.incident_graph import Incident, CallerInfo, CallerRole, IncidentSeverity, IncidentManager


class TestIncident:
    def test_create_incident(self):
        inc = Incident(incident_type="fire", location="123 Main St")
        assert inc.id.startswith("inc_")
        assert inc.status == "active"

    def test_add_caller(self):
        inc = Incident(incident_type="medical", location="456 Oak Ave")
        caller = CallerInfo(role=CallerRole.VICTIM, name="John")
        inc.add_caller(caller)
        assert len(inc.callers) == 1
        assert caller.id in inc.callers

    def test_update_intel(self):
        inc = Incident(incident_type="domestic_violence", location="789 Elm St")
        caller = CallerInfo(role=CallerRole.WITNESS, name="Jane")
        inc.add_caller(caller)
        inc.update_intel(caller.id, "Suspect went to backyard")
        assert "Suspect went to backyard" in inc.callers[caller.id].key_intel

    def test_suspect_info(self):
        inc = Incident(incident_type="robbery", location="100 Bank St")
        inc.update_suspect(description="Male, 6ft, dark jacket", armed=True, weapon_type="handgun")
        assert inc.suspect.armed is True
        assert inc.suspect.weapon_type == "handgun"

    def test_briefing_generation(self):
        inc = Incident(incident_type="fire", severity=IncidentSeverity.HIGH, location="555 Pine St")
        briefing = inc.get_briefing()
        assert "FIRE" in briefing
        assert "555 Pine St" in briefing

    def test_to_dict(self):
        inc = Incident(incident_type="medical", location="Test")
        d = inc.to_dict()
        assert "id" in d
        assert "callers" in d
        assert d["incident_type"] == "medical"


class TestIncidentManager:
    def test_create_and_retrieve(self):
        mgr = IncidentManager()
        inc = mgr.create_incident(incident_type="fire", location="Test")
        retrieved = mgr.get_incident(inc.id)
        assert retrieved is not None
        assert retrieved.id == inc.id

    def test_get_active(self):
        mgr = IncidentManager()
        mgr.create_incident(incident_type="fire", location="A", status="active")
        mgr.create_incident(incident_type="medical", location="B", status="resolved")
        active = mgr.get_active_incidents()
        assert len(active) >= 1
