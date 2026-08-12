import pytest
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.schemas.fact_check import FactCheckRequest, InputType, VerdictType, URLAuthenticityStatus
from app.services.url_authenticity import url_authenticity_service
from app.graph.workflow import orchestrator

@pytest.mark.asyncio
async def test_url_authenticity_nasa():
    """TEST 1: URL = https://www.nasa.gov/ -> Expected status = VERIFIED / AUTHENTIC or TIMEOUT with is_authentic = True"""
    res = await url_authenticity_service.evaluate_url("https://www.nasa.gov/")
    assert res.status in [URLAuthenticityStatus.AUTHENTIC, URLAuthenticityStatus.TIMEOUT]
    assert res.is_authentic is True
    assert "nasa.gov" in res.domain
    assert res.domain_classification == "Official Government Portal"
    assert res.reputation_score >= 90.0

@pytest.mark.asyncio
async def test_url_authenticity_who():
    """TEST 2: URL = https://www.who.int/ -> Expected status = VERIFIED / AUTHENTIC"""
    res = await url_authenticity_service.evaluate_url("https://www.who.int/")
    assert res.status == URLAuthenticityStatus.AUTHENTIC
    assert res.is_authentic is True
    assert "who.int" in res.domain
    assert res.domain_classification == "Official International Organization"
    assert res.reputation_score >= 90.0

@pytest.mark.asyncio
async def test_url_authenticity_invalid_domain():
    """TEST 3: An invalid/nonexistent URL -> Expected status = UNREACHABLE / INVALID"""
    res = await url_authenticity_service.evaluate_url("https://nonexistent-domain-xyz99123887.org")
    assert res.status == URLAuthenticityStatus.UNREACHABLE
    assert res.is_authentic is False
    assert res.is_reachable is False
    assert res.reputation_score == 0.0

@pytest.mark.asyncio
async def test_url_authenticity_decoupled_from_false_claim():
    """
    TEST 4: A valid website containing a false claim.
    Expected: URL status remains AUTHENTIC while individual page claim can be FALSE.
    """
    req = FactCheckRequest(
        input_text="URL: https://www.nasa.gov/\n\nHumans can breathe underwater without any equipment.",
        input_type=InputType.URL
    )
    res = await orchestrator.execute_fact_check(req)
    
    # URL Authenticity Status MUST be Authentic
    assert res.url_authenticity is not None
    assert res.url_authenticity.status == URLAuthenticityStatus.AUTHENTIC
    assert res.url_authenticity.is_authentic is True
    assert "nasa.gov" in res.url_authenticity.domain
    
    # Individual claim verdict MUST NOT override URL authenticity status
    assert len(res.claim_verdicts) > 0
    false_claim_verdict = res.claim_verdicts[0]
    assert false_claim_verdict.verdict in [VerdictType.FALSE, VerdictType.UNCERTAIN, VerdictType.MISLEADING, VerdictType.UNVERIFIED]

@pytest.mark.asyncio
async def test_url_authenticity_timeout_handling(monkeypatch):
    """TEST 5: Request timeout must return TIMEOUT status and not crash or return FALSE."""
    import httpx
    
    async def mock_get(*args, **kwargs):
        raise httpx.TimeoutException("Simulated 15s request timeout")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    res = await url_authenticity_service.evaluate_url("https://slow-responding-domain.org")
    assert res.status == URLAuthenticityStatus.TIMEOUT
    assert res.status != URLAuthenticityStatus.UNREACHABLE
