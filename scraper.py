"""
Website scraper module for the Research & Prospecting Tool.
Scrapes homepage + key subpages to extract company intelligence.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SUBPAGES = [
    "/about", "/about-us", "/customers", "/case-studies", "/case-study",
    "/success-stories", "/testimonials", "/clients", "/why-us", "/solutions",
    "/pricing", "/blog", "/news", "/newsroom", "/press", "/resources",
    "/careers", "/jobs", "/team", "/company"
]

CACHE_DIR = ".cache"
CACHE_TTL = 86400  # 24 hours


def _clean_url(url: str) -> str:
    """Ensure URL has scheme."""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def _extract_text(html: str) -> str:
    """Extract visible text from HTML, removing noise."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _get_cache_path(url: str) -> str:
    """Get cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.json")


def _check_cache(url: str) -> dict | None:
    """Check if valid cache exists for URL."""
    path = _get_cache_path(url)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            cached = json.load(f)
        if time.time() - cached.get("timestamp", 0) < CACHE_TTL:
            return cached.get("data")
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _save_cache(url: str, data: dict):
    """Save scraped data to cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _get_cache_path(url)
    with open(path, "w") as f:
        json.dump({"timestamp": time.time(), "data": data}, f)


def _fetch_page(url: str, timeout: int = 15) -> str | None:
    """Fetch a single page. Returns HTML or None."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except (requests.RequestException, Exception):
        pass
    return None


def _scrape_one_subpage(base_url: str, path: str):
    """Helper for parallel subpage scraping. Returns (path, text) or None."""
    subpage_url = urljoin(base_url, path)
    html = _fetch_page(subpage_url, timeout=10)
    if html:
        text = _extract_text(html)
        if len(text) > 200:
            return (path, text)
    return None


def scrape_website(url: str, use_cache: bool = True) -> dict | None:
    """
    Scrape a company website: homepage + key subpages.

    Returns dict with:
        - url: original URL
        - company_domain: domain name
        - homepage_text: homepage text
        - subpages: {path: text} for found subpages
        - all_text: combined text (capped at 25,000 chars)
        - total_chars: char count
        - pages_found: number of pages scraped
    """
    url = _clean_url(url)

    # Check cache first
    if use_cache:
        cached = _check_cache(url)
        if cached:
            cached["from_cache"] = True
            return cached

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc.replace("www.", "")

    # Scrape homepage
    homepage_html = _fetch_page(url)
    if not homepage_html:
        return None

    homepage_text = _extract_text(homepage_html)
    subpages_found = {}

    # Scrape subpages in parallel for speed
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_scrape_one_subpage, base_url, p) for p in SUBPAGES]
        for future in as_completed(futures):
            result_pair = future.result()
            if result_pair:
                subpages_found[result_pair[0]] = result_pair[1]

    # Combine all text
    all_parts = [f"=== HOMEPAGE ===\n{homepage_text}"]
    for path, text in subpages_found.items():
        all_parts.append(f"=== {path.upper()} ===\n{text}")

    all_text = "\n\n".join(all_parts)
    if len(all_text) > 25000:
        all_text = all_text[:25000]

    result = {
        "url": url,
        "company_domain": domain,
        "homepage_text": homepage_text[:5000],
        "subpages": {k: v[:3000] for k, v in subpages_found.items()},
        "all_text": all_text,
        "total_chars": len(all_text),
        "pages_found": 1 + len(subpages_found),
        "from_cache": False,
    }

    # Only cache if we got meaningful content. Thin scrapes shouldn't poison cache.
    if result["total_chars"] >= 2000:
        _save_cache(url, result)

    return result
