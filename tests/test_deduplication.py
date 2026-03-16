"""Tests for incident deduplication engine."""
import pytest
from core.deduplication import DeduplicationEngine
from core.incident_graph import IncidentManager


class TestDeduplication:
    def test_no_match_for_new_incident(self):
        mgr = IncidentManager()
        engine = DeduplicationEngine(mgr)
        result, score = engine.find_matching_incident(
            location="123 Main St", description="building on fire",
        )
        assert result is None
        assert score == 0.0

    def test_matches_existing_by_location(self):
        mgr = IncidentManager()
        engine = DeduplicationEngine(mgr)
        mgr.create_incident(
            incident_type="fire", location="742 Evergreen Terrace",
            description="house fire with smoke", caller_id="caller-1",
            priority=1,
        )
        result, score = engine.find_matching_incident(
            location="742 Evergreen Terrace",
            description="house fire with smoke visible",
        )
        assert result is not None
        assert score > 0.0

    def test_no_match_different_location(self):
        mgr = IncidentManager()
        engine = DeduplicationEngine(mgr)
        mgr.create_incident(
            incident_type="fire", location="100 North St",
            description="fire", caller_id="caller-1",
        )
        result, score = engine.find_matching_incident(
            location="999 South Ave", description="fire",
        )
        assert result is None

    def test_haversine_distance(self):
        # Same point should be 0
        assert DeduplicationEngine._haversine_distance((40.0, -74.0), (40.0, -74.0)) == 0.0
        # Known distance: ~111km per degree of latitude
        dist = DeduplicationEngine._haversine_distance((40.0, -74.0), (41.0, -74.0))
        assert 110000 < dist < 112000

    def test_text_overlap(self):
        score = DeduplicationEngine._text_overlap(
            "house fire with smoke", "smoke and fire visible",
        )
        assert score > 0.2  # "fire" and "smoke" overlap
        score_none = DeduplicationEngine._text_overlap(
            "car accident", "dog barking",
        )
        assert score_none < 0.2
