import trafilatura
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cloudscraper
from readability import Document
from bs4 import BeautifulSoup
from newspaper import Article as NewspaperArticle
from typing import Optional
import logging
import json
import re
import time
import html as html_module
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Chromium";v="126", "Google Chrome";v="126", "Not=A?Brand";v="8"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Cache-Control": "max-age=0",
    "DNT": "1",
}

# Alternative user-agents for retry
_ALT_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    # Mobile user agents — some sites serve simpler HTML to mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    # Googlebot — many news sites whitelist this
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]


def _fetch_html(url: str) -> str:
    errors = []

    try:
        html = _fetch_with_requests(url)
        if html and len(html) > 500:
            return html
    except Exception as e:
        errors.append(f"requests: {e}")
        logger.debug(f"requests fetch failed: {e}")

    try:
        html = _fetch_with_cloudscraper(url)
        if html and len(html) > 500:
            return html
    except Exception as e:
        errors.append(f"cloudscraper: {e}")
        logger.debug(f"cloudscraper fetch failed: {e}")

    try:
        html = _fetch_with_httpx(url)
        if html and len(html) > 500:
            return html
    except Exception as e:
        errors.append(f"httpx: {e}")
        logger.debug(f"httpx fetch failed: {e}")

    for ua in _ALT_USER_AGENTS:
        try:
            html = _fetch_with_requests(url, user_agent=ua)
            if html and len(html) > 500:
                return html
        except Exception as e:
            errors.append(f"alt-ua: {e}")
            continue

    # Try AMP version of the URL (many news sites have /amp/ endpoints)
    try:
        html = _fetch_amp_version(url)
        if html and len(html) > 500:
            return html
    except Exception as e:
        errors.append(f"amp: {e}")
        logger.debug(f"AMP fetch failed: {e}")

    try:
        html = _fetch_with_google_cache(url)
        if html and len(html) > 500:
            return html
    except Exception as e:
        errors.append(f"google-cache: {e}")
        logger.debug(f"Google cache fetch failed: {e}")

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded and len(downloaded) > 500 and not _is_block_page(downloaded):
            return downloaded
    except Exception as e:
        errors.append(f"trafilatura-fetch: {e}")
        logger.debug(f"trafilatura fetch failed: {e}")

    # Last resort: headless browser (Playwright) — handles JS-rendered sites
    try:
        html = _fetch_with_playwright(url)
        if html and len(html) > 500:
            return html
    except Exception as e:
        errors.append(f"playwright: {e}")
        logger.debug(f"Playwright fetch failed: {e}")

    raise ValueError(f"All fetch strategies failed for {url}: {'; '.join(errors[:5])}")


def _fetch_with_requests(url: str, user_agent: str = None) -> str:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {**_HEADERS}
    if user_agent:
        headers["User-Agent"] = user_agent
    headers["Referer"] = origin

    try:
        session.get(origin, headers=headers, timeout=15, allow_redirects=True)
    except Exception:
        pass

    time.sleep(0.5)

    response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
    response.raise_for_status()

    text = response.text
    if _is_block_page(text):
        raise ValueError("Got a block/captcha page instead of article")

    return text


def _fetch_with_cloudscraper(url: str) -> str:
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )
    response = scraper.get(url, timeout=30, allow_redirects=True)
    response.raise_for_status()

    text = response.text
    if _is_block_page(text):
        raise ValueError("Got a block/captcha page")

    return text


def _fetch_with_httpx(url: str) -> str:
    import httpx

    with httpx.Client(
        headers=_HEADERS,
        follow_redirects=True,
        timeout=30.0,
        http2=True,
    ) as client:
        response = client.get(url)
        response.raise_for_status()

        text = response.text
        if _is_block_page(text):
            raise ValueError("Got a block/captcha page")

        return text


def _fetch_with_google_cache(url: str) -> str:
    encoded = quote(url, safe="")
    cache_urls = [
        f"https://webcache.googleusercontent.com/search?q=cache:{encoded}",
        f"https://web.archive.org/web/2026/{url}",
        f"https://web.archive.org/web/2025/{url}",
        f"https://web.archive.org/web/2024/{url}",
    ]
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.5)))

    for cache_url in cache_urls:
        try:
            response = session.get(
                cache_url,
                headers={"User-Agent": _HEADERS["User-Agent"]},
                timeout=20,
                allow_redirects=True,
            )
            if response.status_code == 200 and len(response.text) > 500:
                text = response.text
                if not _is_block_page(text):
                    logger.info(f"Fetched from cache/archive: {cache_url}")
                    return text
        except Exception:
            continue

    raise ValueError("No cache/archive available")


def _fetch_amp_version(url: str) -> str:
    """Try to fetch an AMP version of the URL — many news sites have cleaner AMP pages."""
    parsed = urlparse(url)
    
    # Strategy 1: append /amp to the path
    amp_urls = []
    path = parsed.path.rstrip("/")
    amp_urls.append(f"{parsed.scheme}://{parsed.netloc}{path}/amp")
    amp_urls.append(f"{parsed.scheme}://{parsed.netloc}{path}/amp/")
    
    # Strategy 2: Google AMP cache
    amp_urls.append(f"https://{parsed.netloc.replace('.', '-')}.cdn.ampproject.org/v/s/{parsed.netloc}{parsed.path}")
    
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=1, backoff_factor=0.5)))
    
    for amp_url in amp_urls:
        try:
            response = session.get(
                amp_url,
                headers={"User-Agent": _HEADERS["User-Agent"]},
                timeout=15,
                allow_redirects=True,
            )
            if response.status_code == 200 and len(response.text) > 500:
                text = response.text
                if not _is_block_page(text):
                    logger.info(f"Fetched AMP version: {amp_url}")
                    return text
        except Exception:
            continue

    raise ValueError("No AMP version available")


def _fetch_with_playwright(url: str) -> str:
    """Fetch page using headless Chromium — handles JS-rendered sites like The Wire."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ValueError("Playwright not installed")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                user_agent=_HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait a bit for JS to render content
            page.wait_for_timeout(3000)
            html = page.content()
            if _is_block_page(html):
                raise ValueError("Playwright got a block page")
            logger.info(f"Playwright fetched {len(html)} bytes from {url}")
            return html
        finally:
            browser.close()


def _is_block_page(html: str) -> bool:
    if not html or len(html) < 200:
        return True

    lower = html.lower()
    
    # If page has ld+json with articleBody, it's definitely not a block page
    if '"articlebody"' in lower or '"article_body"' in lower:
        return False

    block_signals = [
        "access denied",
        "403 forbidden",
        "captcha",
        "please verify you are a human",
        "checking your browser",
        "enable javascript and cookies",
        "ray id",
        "just a moment",
        "bot detection",
    ]

    signal_count = sum(1 for s in block_signals if s in lower)
    if signal_count >= 2:
        return True
    if len(html) < 1000 and signal_count >= 1:
        return True

    return False


def extract_from_url(url: str) -> dict:
    """Extract article content from a URL using multi-strategy fetching + multi-method extraction.
    
    Tries all extraction methods and picks the one that produces the most text,
    ensuring we don't settle for a short snippet when a better extraction exists.
    """
    result = {"title": "", "text": "", "author": "", "date": "", "source": url}

    # Step 1: Fetch HTML with fallback strategies
    html = None
    try:
        html = _fetch_html(url)
        logger.info(f"Fetched {len(html)} bytes from {url}")
    except Exception as e:
        logger.warning(f"All HTML fetch strategies failed: {e}")

    # Collect all extraction candidates: (text, title, author, date, method)
    candidates = []

    # Method 0: Extract from ld+json articleBody (works for SPAs like The Wire, some Indian sites)
    if html:
        try:
            ld_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
            for block in ld_blocks:
                try:
                    ld = json.loads(block)
                    # Flatten: handle direct object, list, or @graph wrapper
                    items = []
                    if isinstance(ld, dict):
                        if "@graph" in ld:
                            items = ld["@graph"] if isinstance(ld["@graph"], list) else [ld["@graph"]]
                        else:
                            items = [ld]
                    elif isinstance(ld, list):
                        items = ld
                    
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        body = item.get("articleBody", "") or item.get("text", "")
                        if body and len(body.strip()) > 100:
                            author = item.get("author", "")
                            if isinstance(author, dict):
                                author_str = author.get("name", "")
                            elif isinstance(author, list) and author:
                                author_str = author[0].get("name", "") if isinstance(author[0], dict) else str(author[0])
                            else:
                                author_str = str(author) if author else ""
                            candidates.append({
                                "text": body.strip(),
                                "title": item.get("headline", "") or _extract_title_from_html(html),
                                "author": author_str,
                                "date": item.get("datePublished", ""),
                                "method": "ld+json",
                            })
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception as e:
            logger.warning(f"ld+json extraction failed: {e}")

    # Method 1: newspaper3k with pre-fetched HTML
    if html:
        try:
            article = NewspaperArticle(url, browser_user_agent=_HEADERS["User-Agent"])
            article.set_html(html)
            article.parse()
            if article.text and len(article.text.strip()) > 100:
                candidates.append({
                    "text": article.text.strip(),
                    "title": article.title or _extract_title_from_html(html),
                    "author": ", ".join(article.authors) if article.authors else "",
                    "date": str(article.publish_date) if article.publish_date else "",
                    "method": "newspaper3k",
                })
        except Exception as e:
            logger.warning(f"newspaper3k extraction failed: {e}")

    # Method 1b: newspaper3k self-download fallback (if our fetch failed)
    if not html:
        try:
            article = NewspaperArticle(url, browser_user_agent=_HEADERS["User-Agent"], request_timeout=20)
            article.download()
            article.parse()
            if article.text and len(article.text.strip()) > 100:
                candidates.append({
                    "text": article.text.strip(),
                    "title": article.title or "",
                    "author": ", ".join(article.authors) if article.authors else "",
                    "date": str(article.publish_date) if article.publish_date else "",
                    "method": "newspaper3k-download",
                })
        except Exception as e:
            logger.warning(f"newspaper3k self-download failed: {e}")

    # Method 2: trafilatura
    if html:
        try:
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
            )
            traf_title = ""
            traf_author = ""
            traf_date = ""
            try:
                metadata_raw = trafilatura.extract(
                    html,
                    include_comments=False,
                    output_format="json",
                    with_metadata=True,
                )
                meta = json.loads(metadata_raw) if metadata_raw else {}
                traf_title = meta.get("title", "")
                traf_author = meta.get("author", "")
                traf_date = meta.get("date", "")
            except (json.JSONDecodeError, TypeError):
                pass

            if text and len(text.strip()) > 100:
                candidates.append({
                    "text": text.strip(),
                    "title": traf_title or _extract_title_from_html(html),
                    "author": traf_author,
                    "date": traf_date,
                    "method": "trafilatura",
                })
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")

    # Method 3: readability-lxml
    if html:
        try:
            doc = Document(html)
            read_title = doc.title() or _extract_title_from_html(html)
            soup = BeautifulSoup(doc.summary(), "html.parser")
            read_text = soup.get_text(separator="\n", strip=True)

            if read_text and len(read_text.strip()) > 100:
                candidates.append({
                    "text": read_text.strip(),
                    "title": read_title,
                    "author": "",
                    "date": "",
                    "method": "readability",
                })
        except Exception as e:
            logger.warning(f"Readability extraction failed: {e}")

    # Method 4: Raw BeautifulSoup — last resort, grab <article> or <p> tags
    if html:
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Try <article> tag first
            article_tag = soup.find("article")
            if article_tag:
                paragraphs = article_tag.find_all("p")
                text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if text and len(text.strip()) > 100:
                    candidates.append({
                        "text": text.strip(),
                        "title": _extract_title_from_html(html),
                        "author": "",
                        "date": "",
                        "method": "bs4-article",
                    })

            # Try all <p> tags with filtering
            paragraphs = soup.find_all("p")
            good_paragraphs = []
            for p in paragraphs:
                parent_classes = " ".join(p.parent.get("class", [])).lower() if p.parent else ""
                if any(skip in parent_classes for skip in ["nav", "footer", "sidebar", "menu", "comment", "cookie"]):
                    continue
                text_content = p.get_text(strip=True)
                if len(text_content) > 40:
                    good_paragraphs.append(text_content)

            if good_paragraphs and len("\n".join(good_paragraphs)) > 100:
                candidates.append({
                    "text": "\n".join(good_paragraphs).strip(),
                    "title": _extract_title_from_html(html),
                    "author": "",
                    "date": "",
                    "method": "bs4-ptags",
                })

        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed: {e}")

    # Pick the best candidate — longest text wins
    if not candidates:
        raise ValueError(f"Could not extract article from URL: {url}")

    best = max(candidates, key=lambda c: len(c["text"]))
    logger.info(f"Best extraction: {best['method']} ({len(best['text'])} chars) out of {len(candidates)} candidates")

    # Clean text: unescape HTML entities, normalize whitespace
    result["text"] = _clean_text(best["text"])
    result["title"] = _clean_text(best["title"]) or "Untitled Article"
    result["author"] = _clean_text(best["author"])
    result["date"] = best["date"]
    result["extraction_method"] = best["method"]

    return result


def _clean_text(text: str) -> str:
    """Clean extracted text: unescape HTML entities, normalize whitespace."""
    if not text:
        return text
    # Double-unescape for double-encoded entities (e.g. &amp;#039; -> &#039; -> ')
    cleaned = html_module.unescape(html_module.unescape(text))
    # Normalize whitespace but keep paragraph breaks
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def _extract_title_from_html(html: str) -> str:
    """Extract title from HTML using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Try og:title first (most reliable for news)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try <title> tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove common suffixes like " - BBC News", " | Reuters"
            for sep in [" - ", " | ", " – ", " — "]:
                if sep in title:
                    title = title.split(sep)[0].strip()
            return title

        # Try <h1> tag
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(strip=True)
    except Exception:
        pass
    return "Untitled Article"


def extract_from_text(text: str, title: Optional[str] = None) -> dict:
    """Process raw text input."""
    lines = text.strip().split("\n")
    detected_title = title or (lines[0][:100] if lines else "Untitled")
    body = "\n".join(lines[1:]) if len(lines) > 1 and not title else text

    return {
        "title": detected_title,
        "text": body.strip(),
        "author": "",
        "date": "",
        "source": "direct_input",
    }
