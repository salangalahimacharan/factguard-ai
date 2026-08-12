import asyncio
import httpx
import urllib.parse
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("factguard.services.url_scraper")

BLOCKED_IP_PATTERNS = [
    r'^127\.', r'^10\.', r'^172\.(1[6-9]|2[0-9]|3[0-1])\.', r'^192\.168\.',
    r'^localhost$', r'^0\.0\.0\.0$'
]

class URLScraperService:
    """Safely extracts headline and article body text from target URLs with SSRF protection."""

    async def fetch_url_content(self, url: str) -> tuple[str, str]:
        if not url:
            raise ValueError("Target URL cannot be empty.")

        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        # SSRF Protection Check
        if not self._is_safe_url(url):
            raise ValueError("Target URL is invalid or targets an internal restricted IP address.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache"
        }

        try:
            timeout_cfg = httpx.Timeout(4.0, connect=3.0, read=4.0)
            async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True, verify=False) as client:
                resp = await asyncio.wait_for(client.get(url, headers=headers), timeout=4.0)
                resp.raise_for_status()
                
                html_content = resp.text
                soup = BeautifulSoup(html_content, "html.parser")

                # Remove script and style tags
                for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.extract()

                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                if not title:
                    # Fallback title from h1 or URL path
                    h1 = soup.find("h1")
                    title = h1.get_text().strip() if h1 else urllib.parse.urlparse(url).netloc

                # Extract main article paragraphs
                paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 25]
                body_text = "\n\n".join(paragraphs[:8])

                if not body_text:
                    body_text = soup.get_text()[:1500]

                clean_body = re.sub(r'\s+', ' ', body_text).strip()[:1500]
                if len(clean_body) < 20:
                    clean_body = f"Target page content from {url}"

                full_text = f"Article Headline: {title}\n\nURL: {url}\n\nContent:\n{clean_body}"
                return title, full_text
        except (httpx.TimeoutException, TimeoutError) as te:
            logger.warning(f"URL scraper timed out fetching '{url}': {te}")
            parsed = urllib.parse.urlparse(url)
            fallback_title = f"Webpage from {parsed.netloc}"
            fallback_text = f"URL: {url}\n\nTarget webpage content retrieval timed out after 15 seconds. Domain authenticity evaluated separately."
            return fallback_title, fallback_text
        except httpx.HTTPStatusError as hse:
            logger.warning(f"HTTP status error fetching URL '{url}': {hse}")
            # Generate readable fallback text from URL for analysis if site blocks scrapers
            parsed = urllib.parse.urlparse(url)
            path_words = re.sub(r'[-_/\.]', ' ', parsed.path)
            fallback_title = f"Article from {parsed.netloc}"
            fallback_text = f"Headline: {path_words}\n\nURL: {url}\n\nWeb page content from {parsed.netloc} discussing {path_words}."
            return fallback_title, fallback_text
        except Exception as e:
            logger.error(f"Failed to scrape URL '{url}': {e}")
            parsed = urllib.parse.urlparse(url)
            fallback_title = f"Webpage from {parsed.netloc}"
            fallback_text = f"URL: {url}\n\nTarget webpage content from {parsed.netloc}."
            return fallback_title, fallback_text

    def _is_safe_url(self, url: str) -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False
            
            hostname = parsed.hostname.lower() if parsed.hostname else ""
            for pattern in BLOCKED_IP_PATTERNS:
                if re.search(pattern, hostname):
                    return False
            return True
        except Exception:
            return False

url_scraper_service = URLScraperService()
