"""
Multi-Caller Deduplication Engine.
Clusters calls about the same incident into a single Incident.
"""
import time
import math
from typing import Optional
from core.incident_graph import IncidentManager, Incident
from core.config import settings


class DeduplicationEngine:

    def __init__(self, incident_manager: IncidentManager):
        self.im = incident_manager

    def find_matching_incident(
        self,
        location: str,
        location_coords: Optional[tuple] = None,
        description: str = "",
        call_time: float = None,
    ) -> Optional[Incident]:
        if call_time is None:
            call_time = time.time()

        active = self.im.get_active_incidents()
        best_match = None
        best_score = 0.0

        for incident in active:
            score = 0.0
            age_minutes = (call_time - incident.created_at) / 60
            if age_minutes > 30:
                continue

            if location_coords and incident.location_coords:
                dist = self._haversine_distance(location_coords, incident.location_coords)
                if dist < settings.INCIDENT_RADIUS_METERS:
                    score += 0.5
                elif dist < settings.INCIDENT_RADIUS_METERS * 3:
                    score += 0.2
            elif location and incident.location:
                overlap = self._text_overlap(location.lower(), incident.location.lower())
                score += overlap * 0.4

            if description and incident.summary:
                desc_overlap = self._text_overlap(description.lower(), incident.summary.lower())
                score += desc_overlap * 0.3

            recency_bonus = max(0, 1 - (age_minutes / 30)) * 0.2
            score += recency_bonus

            if score > best_score:
                best_score = score
                best_match = incident

        if best_score >= settings.DEDUP_SIMILARITY_THRESHOLD:
            return best_match
        return None

    @staticmethod
    def _haversine_distance(coord1: tuple, coord2: tuple) -> float:
        R = 6371000
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    @staticmethod
    def _text_overlap(text_a: str, text_b: str) -> float:
        words_a = set(text_a.split())
        words_b = set(text_b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0
