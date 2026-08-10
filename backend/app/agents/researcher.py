import asyncio
import time
import logging
import httpx
import urllib.parse
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from app.schemas.fact_check import ClaimExtractionItem, SourceMetadata, CredibilityRating
from app.config import settings

logger = logging.getLogger("factguard.agents.researcher")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class ResearchAgent:
    """Agent 2: Multi-engine web researcher using live DuckDuckGo, Wikipedia, Google News, and Tavily APIs."""

    async def run(self, claim: ClaimExtractionItem) -> List[SourceMetadata]:
        start_time = time.time()
        logger.info(f"Agent 2 [Researcher] researching claim {claim.claim_id}: '{claim.claim_text}'")

        # Generate targeted search query strategies
        queries = self._generate_search_queries(claim)
        
        raw_results: List[Dict[str, Any]] = []

        # Execute search query variations
        for query_type, q in queries.items():
            results = await self._execute_search(q, query_type)
            raw_results.extend(results)

        # Deduplicate results by normalized URL
        seen_urls = set()
        sources: List[SourceMetadata] = []
        
        for idx, res in enumerate(raw_results):
            url = res.get("url", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            # Determine publisher & source type from URL
            domain = self._extract_domain(url)
            publisher = res.get("publisher") or domain
            source_type = self._determine_source_type(domain)

            sources.append(SourceMetadata(
                source_id=f"SRC-{claim.claim_id}-{len(sources)+1:02d}",
                claim_id=claim.claim_id,
                title=res.get("title", f"Information regarding {domain}"),
                url=url,
                publisher=publisher,
                publication_date=res.get("date"),
                excerpt=res.get("snippet", claim.claim_text)[:500],
                source_type=source_type,
                credibility_score=50.0, # Refined by Source Credibility Agent
                credibility_rating=CredibilityRating.MEDIUM,
                reliability_indicators=[f"Type: {source_type}", f"Domain: {domain}"]
            ))

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 2 [Researcher] found {len(sources)} unique sources for claim {claim.claim_id} in {elapsed}ms.")
        return sources

    def _generate_search_queries(self, claim: ClaimExtractionItem) -> Dict[str, str]:
        claim_text = claim.claim_text
        entities_str = " ".join(claim.entities[:3]) if claim.entities else ""
        date_str = " ".join(claim.dates[:1]) if claim.dates else ""

        # Clean search terms without quotes or generic dictionary prefixes
        clean_text = re.sub(r'[^\w\s]', '', claim_text)

        return {
            "entity_event": f"{entities_str} {clean_text[:60]}".strip(),
            "claim_date": f"{clean_text[:50]} {date_str}".strip(),
            "primary_source": f"NASA press release study {entities_str} {clean_text[:40]}".strip(),
            "contradiction": f"{clean_text[:50]} debunk myth fake".strip(),
        }

    async def _execute_search(self, query: str, query_type: str) -> List[Dict[str, Any]]:
        results = []
        
        # Engine 1: DuckDuckGo HTML Direct Scraper
        try:
            ddg_results = await self._search_duckduckgo_html(query)
            if ddg_results:
                results.extend(ddg_results)
        except Exception as e:
            logger.debug(f"DuckDuckGo HTML search exception for '{query}': {e}")

        # Engine 2: Wikipedia Search API
        try:
            wiki_results = await self._search_wikipedia(query)
            if wiki_results:
                results.extend(wiki_results)
        except Exception as e:
            logger.debug(f"Wikipedia API exception for '{query}': {e}")

        # Engine 3: Google News RSS
        if not results:
            try:
                gnews_results = await self._search_google_news_rss(query)
                if gnews_results:
                    results.extend(gnews_results)
            except Exception as e:
                logger.debug(f"Google News RSS exception for '{query}': {e}")

        return results[:3] # Limit per query variation

    async def _search_duckduckgo_html(self, query: str) -> List[Dict[str, Any]]:
        results = []
        headers = {"User-Agent": USER_AGENT}
        payload = {"q": query}

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.post("https://html.duckduckgo.com/html/", data=payload, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                a_tags = soup.find_all("a", class_="result__a")
                snippet_tags = soup.find_all("a", class_="result__snippet")

                for a, snippet in zip(a_tags[:4], snippet_tags[:4]):
                    raw_url = a.get("href", "")
                    clean_url = self._decode_ddg_url(raw_url)
                    
                    if clean_url and not any(dict_domain in clean_url for dict_domain in ["dictionary.cambridge.org", "merriam-webster.com"]):
                        results.append({
                            "title": a.get_text().strip(),
                            "url": clean_url,
                            "snippet": snippet.get_text().strip(),
                            "publisher": self._extract_domain(clean_url),
                            "date": None
                        })
        return results

    async def _search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        results = []
        headers = {"User-Agent": "FactGuardAI/1.0 (contact@factguard.org)"}
        encoded = urllib.parse.quote_plus(query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("query", {}).get("search", [])
                for hit in hits[:2]:
                    title = hit.get("title", "")
                    snippet = hit.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    results.append({
                        "title": f"Wikipedia: {title}",
                        "url": page_url,
                        "snippet": snippet,
                        "publisher": "wikipedia.org",
                        "date": None
                    })
        return results

    async def _search_google_news_rss(self, query: str) -> List[Dict[str, Any]]:
        results = []
        headers = {"User-Agent": USER_AGENT}
        encoded = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "xml")
                items = soup.find_all("item")
                for item in items[:3]:
                    link = item.link.text if item.link else ""
                    results.append({
                        "title": item.title.text if item.title else "News Article",
                        "url": link,
                        "snippet": f"Google News: {item.title.text if item.title else ''}",
                        "publisher": self._extract_domain(link),
                        "date": item.pubDate.text if item.pubDate else None
                    })
        return results

    def _decode_ddg_url(self, raw_url: str) -> str:
        try:
            if "uddg=" in raw_url:
                parsed = urllib.parse.urlparse(raw_url)
                qs = urllib.parse.parse_qs(parsed.query)
                if "uddg" in qs:
                    return qs["uddg"][0]
            if raw_url.startswith("//"):
                return "https:" + raw_url
            return raw_url
        except Exception:
            return raw_url

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain or "web-source"
        except Exception:
            return "web-source"

    def _determine_source_type(self, domain: str) -> str:
        if domain.endswith(".gov") or "who.int" in domain or "cdc.gov" in domain or "nasa.gov" in domain:
            return "official"
        elif domain.endswith(".edu") or "arxiv.org" in domain or "nature.com" in domain or "sciencedirect.com" in domain:
            return "academic"
        elif any(news in domain for news in ["reuters.com", "apnews.com", "bbc.com", "nytimes.com", "bloomberg.com", "theguardian.com"]):
            return "news"
        elif "wikipedia.org" in domain:
            return "encyclopedia"
        else:
            return "web"

research_agent = ResearchAgent()
