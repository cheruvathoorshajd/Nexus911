"""Tests for multi-caller deduplication."""
import pytest
from core.incident_graph import IncidentManager, IncidentSeverity
from core.deduplication import DeduplicationEngine


class TestDeduplication:
    def test_no_match_for_new_incident(self):
        mgr = IncidentManager()
        engine = DeduplicationEngine(mgr)
        result = engine.find_matching_incident(location="123 New St", description="fire")
        assert result is None

    def test_matches_existing_by_location(self):
        mgr = IncidentManager()
        engine = DeduplicationEngine(mgr)
        mgr.create_incident(
            incident_type="fire", location="742 Evergreen Terrace",
            severity=IncidentSeverity.HIGH, summary="house fire with smoke",
        )
        result = engine.find_matching_incident(
            location="742 Evergreen Terrace", description="fire at house",
        )
        assert result is not None

    def test_no_match_different_location(self):
        mgr = IncidentManager()
        engine = DeduplicationEngine(mgr)
        mgr.create_incident(incident_type="fire", location="100 North St", summary="fire")
        result = engine.find_matching_incident(location="999 South Ave", description="car accident")
        assert result is None

    def test_haversine_distance(self):
        dist = DeduplicationEngine._haversine_distance((42.3601, -71.0589), (42.3611, -71.0579))
        assert dist < 200  # Should be ~130 meters

    def test_text_overlap(self):
        score = DeduplicationEngine._text_overlap("fire at house on elm", "house fire on elm street")
        assert score > 0.4
