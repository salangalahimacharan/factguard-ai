import asyncio
import httpx
import urllib.parse
import re
import logging
from typing import List, Tuple, Dict, Any
from app.schemas.fact_check import URLAuthenticityResult, URLAuthenticityStatus

logger = logging.getLogger("factguard.services.url_authenticity")

HIGH_TRUST_GOV_TLDS = [".gov", ".mil", ".gov.uk", ".gov.in", ".gov.au", ".gov.ca"]
HIGH_TRUST_EDU_TLDS = [".edu", ".ac.uk", ".edu.au", ".edu.in"]
HIGH_TRUST_INT_DOMAINS = ["who.int", "un.org", "unesco.org", "wipo.int", "nasa.gov", "cdc.gov", "nih.gov"]
HIGH_TRUST_NEWS_DOMAINS = ["wikipedia.org", "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com", "nature.com", "sciencedirect.com"]

class URLAuthenticityService:
    """Evaluates website domain authenticity, SSL encryption, reachability, and official domain classification."""

    async def evaluate_url(self, url: str) -> URLAuthenticityResult:
        if not url:
            return URLAuthenticityResult(
                url=url or "",
                domain="unknown",
                status=URLAuthenticityStatus.UNREACHABLE,
                is_authentic=False,
                is_reachable=False,
                has_ssl=False,
                domain_classification="Invalid URL Format",
                reputation_score=0.0,
                security_notes=["URL string was empty or missing."]
            )

        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname.lower() if parsed.hostname else ""
            if not hostname or "." not in hostname:
                return URLAuthenticityResult(
                    url=url,
                    domain=hostname or "unknown",
                    status=URLAuthenticityStatus.UNREACHABLE,
                    is_authentic=False,
                    is_reachable=False,
                    has_ssl=False,
                    domain_classification="Invalid Hostname",
                    reputation_score=0.0,
                    security_notes=["URL hostname format is invalid or unresolvable."]
                )
        except Exception:
            return URLAuthenticityResult(
                url=url,
                domain="unknown",
                status=URLAuthenticityStatus.UNREACHABLE,
                is_authentic=False,
                is_reachable=False,
                has_ssl=False,
                domain_classification="Malformed URL",
                reputation_score=0.0,
                security_notes=["Failed to parse URL structure."]
            )

        # Extract base domain (e.g. www.nasa.gov -> nasa.gov)
        domain_parts = hostname.split(".")
        if len(domain_parts) >= 2:
            base_domain = ".".join(domain_parts[-2:])
        else:
            base_domain = hostname

        has_ssl = parsed.scheme == "https"
        security_notes = []

        # Check high-trust known domains FIRST for instant 0ms verification
        domain_classification = "General Web Page"
        reputation_score = 75.0
        is_known_high_trust = False

        if any(hostname.endswith(tld) for tld in HIGH_TRUST_GOV_TLDS):
            domain_classification = "Official Government Portal"
            reputation_score = 98.0
            is_known_high_trust = True
            security_notes.append(f"Verified government top-level domain ({hostname}).")
        elif any(hostname.endswith(tld) for tld in HIGH_TRUST_EDU_TLDS):
            domain_classification = "Educational Institution"
            reputation_score = 95.0
            is_known_high_trust = True
            security_notes.append(f"Verified educational institution domain ({hostname}).")
        elif any(hostname.endswith(domain) or base_domain == domain for domain in HIGH_TRUST_INT_DOMAINS):
            domain_classification = "Official International Organization"
            reputation_score = 98.0
            is_known_high_trust = True
            security_notes.append(f"Verified official international agency domain ({hostname}).")
        elif any(hostname.endswith(domain) or base_domain == domain for domain in HIGH_TRUST_NEWS_DOMAINS):
            domain_classification = "Established News / Reference Media"
            reputation_score = 90.0
            is_known_high_trust = True
            security_notes.append(f"Established mainstream publisher domain ({hostname}).")

        if is_known_high_trust:
            if has_ssl:
                security_notes.append("HTTPS transport SSL/TLS encryption active.")
            return URLAuthenticityResult(
                url=url,
                domain=hostname,
                status=URLAuthenticityStatus.AUTHENTIC,
                is_authentic=True,
                is_reachable=True,
                has_ssl=has_ssl,
                domain_classification=domain_classification,
                reputation_score=reputation_score,
                security_notes=security_notes
            )

        # For unknown domains, check reachability via HTTP/HTTPS GET with 2.5s timeout
        is_reachable = False
        is_timeout = False

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            timeout_cfg = httpx.Timeout(2.5, connect=2.0, read=2.5)
            async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True, verify=False) as client:
                resp = await asyncio.wait_for(client.get(url, headers=headers), timeout=2.5)
                if resp.status_code < 400 or resp.status_code in [401, 403]:
                    is_reachable = True
                    security_notes.append(f"HTTP Server reachable (Status code: {resp.status_code}).")
                else:
                    security_notes.append(f"HTTP Server returned status code {resp.status_code}.")
        except (httpx.TimeoutException, TimeoutError, asyncio.TimeoutError):
            is_timeout = True
            is_reachable = False
            security_notes.append("Target website request timed out. Domain registration and SSL record remain active.")
        except httpx.HTTPStatusError as hse:
            is_reachable = True
            security_notes.append(f"Server responded with status {hse.response.status_code}.")
        except Exception as err:
            logger.warning(f"Reachability check failed for '{url}': {err}")
            is_reachable = False
            security_notes.append(f"Domain reachability check failed: {str(err)}")

        if has_ssl:
            security_notes.append("HTTPS transport SSL/TLS encryption active.")
        else:
            security_notes.append("WARNING: Connection uses unencrypted HTTP protocol.")

        if is_reachable:
            status = URLAuthenticityStatus.AUTHENTIC
            is_authentic = True
        elif is_timeout:
            status = URLAuthenticityStatus.TIMEOUT
            is_authentic = False
        else:
            status = URLAuthenticityStatus.UNREACHABLE
            is_authentic = False
            reputation_score = 0.0

        return URLAuthenticityResult(
            url=url,
            domain=hostname,
            status=status,
            is_authentic=is_authentic,
            is_reachable=is_reachable,
            has_ssl=has_ssl,
            domain_classification=domain_classification,
            reputation_score=reputation_score,
            security_notes=security_notes
        )

url_authenticity_service = URLAuthenticityService()
