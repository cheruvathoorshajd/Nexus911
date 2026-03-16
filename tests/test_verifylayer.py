"""
Unit tests for the VerifyLayer verification system.

Tests models, penalization engine, cache, and integration.
Run with: pytest nexus911/tests/test_verifylayer.py -v
"""
import pytest
import asyncio
from verification.models import (
    ExtractedFact,
    NLIResult,
    NLILabel,
    FactConfidence,
    ContradictionReport,
    CallerRole,
    VerificationResult,
    CacheStats,
)
from verification.penalization import PenalizationEngine, CALLER_CREDIBILITY
from verification.cache import AsyncLRUCache


class TestModels:
    """Test Pydantic model creation and validation."""

    def test_extracted_fact_auto_id(self):
        fact = ExtractedFact(
            incident_id="INC-001",
            caller_id="caller-1",
            fact_text="Red car on Main Street",
        )
        assert fact.fact_id != ""
        assert len(fact.fact_id) == 16

    def test_extracted_fact_deterministic_id(self):
        fact1 = ExtractedFact(
            incident_id="INC-001",
            caller_id="caller-1",
            fact_text="Red car on Main Street",
        )
        fact2 = ExtractedFact(
            incident_id="INC-001",
            caller_id="caller-2",
            fact_text="Red car on Main Street",
        )
        # Same incident + same fact text = same fact_id
        assert fact1.fact_id == fact2.fact_id

    def test_nli_result_defaults(self):
        result = NLIResult()
        assert result.label == NLILabel.NEUTRAL
        assert result.score == 0.0

    def test_contradiction_report(self):
        report = ContradictionReport(
            fact_a_id="abc",
            fact_b_id="def",
            fact_a_text="Red car",
            fact_b_text="Blue car",
            caller_a="caller-1",
            caller_b="caller-2",
            severity=0.8,
        )
        assert report.severity == 0.8


class TestPenalization:
    """Test the confidence scoring engine."""

    def setup_method(self):
        self.engine = PenalizationEngine()

    def test_high_confidence_entailment(self):
        nli = NLIResult(label=NLILabel.ENTAILMENT, score=0.9)
        score = self.engine.score(nli, "official", [])
        assert score.overall > 0.5
        assert score.nli_score == 0.9

    def test_contradiction_penalty(self):
        nli = NLIResult(label=NLILabel.ENTAILMENT, score=0.9)
        contradiction = ContradictionReport(
            fact_a_id="a", fact_b_id="b",
            fact_a_text="x", fact_b_text="y",
            caller_a="c1", caller_b="c2",
            severity=0.9,
        )
        score = self.engine.score(nli, "witness", [contradiction])
        assert score.contradiction_penalty > 0

    def test_child_lower_credibility(self):
        nli = NLIResult(label=NLILabel.ENTAILMENT, score=0.5)
        child_score = self.engine.score(nli, "child", [])
        official_score = self.engine.score(nli, "official", [])
        assert child_score.caller_credibility < official_score.caller_credibility

    def test_corroboration_bonus(self):
        nli = NLIResult(label=NLILabel.ENTAILMENT, score=0.5)
        no_corr = self.engine.score(nli, "witness", [], corroborating_callers=0)
        with_corr = self.engine.score(nli, "witness", [], corroborating_callers=3)
        assert with_corr.overall > no_corr.overall

    def test_caller_credibility_weights(self):
        """Verify all caller roles have defined credibility weights."""
        for role in CallerRole:
            assert role in CALLER_CREDIBILITY


class TestCache:
    """Test the async LRU cache."""

    @pytest.fixture
    def cache(self):
        return AsyncLRUCache(max_size=3, ttl_seconds=60.0)

    @pytest.fixture
    def sample_result(self):
        return VerificationResult(
            fact=ExtractedFact(
                incident_id="INC-001",
                caller_id="caller-1",
                fact_text="Test fact",
            ),
        )

    @pytest.mark.asyncio
    async def test_put_and_get(self, cache, sample_result):
        await cache.put("fact-1", sample_result)
        result = await cache.get("fact-1")
        assert result is not None
        assert result.from_cache is True

    @pytest.mark.asyncio
    async def test_miss(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_eviction(self, cache, sample_result):
        await cache.put("a", sample_result)
        await cache.put("b", sample_result)
        await cache.put("c", sample_result)
        await cache.put("d", sample_result)  # Should evict "a"
        assert await cache.get("a") is None
        assert await cache.get("d") is not None

    @pytest.mark.asyncio
    async def test_stats(self, cache, sample_result):
        await cache.put("x", sample_result)
        await cache.get("x")  # hit
        await cache.get("y")  # miss
        stats = await cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
