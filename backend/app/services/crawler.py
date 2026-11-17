"""Polite, robust crawler engine:
- Respects robots.txt and rate limits (CRAWL_DELAY)
- Dual mode: RSS feed parsing first, HTML article extraction via trafilatura fallback
- Change detection via SHA-256 content hashing (skips existing content hashes)
- Persists new documents to documents table
- Logs every attempt to crawl_runs and updates sources last_checked/last_status_code
- Zero unhandled exceptions: one failing source never breaks the batch.
"""

from datetime import datetime, timezone
import hashlib
import logging
import time
import urllib.parse
import urllib.robotparser as rp
from typing import Optional

from bs4 import BeautifulSoup
import feedparser
import requests
import trafilatura

from ..config import CRAWL_DELAY, USER_AGENT
from ..db import get_conn, query

log = logging.getLogger(__name__)


def is_allowed_by_robots(url: str) -> bool:
    """Check robots.txt compliance for given URL."""
    try:
        p = urllib.parse.urlparse(url)
        robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
        parser = rp.RobotFileParser()
        parser.set_url(robots_url)
        parser.read()
        return parser.can_fetch(USER_AGENT, url)
    except Exception as exc:
        log.debug("robots.txt check failed for %s: %s (defaulting to allowed)", url, exc)
        return True


def _parse_published_date(raw_date: Optional[str]) -> Optional[datetime]:
    """Parse various date string formats into UTC datetime."""
    if not raw_date:
        return None
    try:
        from dateutil import parser as dt_parser
        dt = dt_parser.parse(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _fetch_rss(url: str) -> Optional[list[dict]]:
    """Try to parse the URL as an RSS or Atom feed."""
    try:
        # Check if URL looks like an RSS feed, or probe feedparser
        feed = feedparser.parse(url, agent=USER_AGENT)
        if feed.bozo == 0 and len(feed.entries) > 0:
            docs = []
            for entry in feed.entries[:10]:  # up to 10 latest entries per feed
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", url).strip()
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                content_list = getattr(entry, "content", [])
                full_text = content_list[0].value if content_list else summary

                clean_text = trafilatura.extract(full_text) or BeautifulSoup(full_text, "html.parser").get_text(separator=" ").strip()
                if not clean_text:
                    clean_text = title

                pub_date = None
                if hasattr(entry, "published"):
                    pub_date = _parse_published_date(entry.published)
                elif hasattr(entry, "updated"):
                    pub_date = _parse_published_date(entry.updated)

                if clean_text:
                    h = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
                    docs.append({
                        "url": link,
                        "title": title or "Feed Update",
                        "content": clean_text,
                        "content_hash": h,
                        "published_at": pub_date
                    })
            return docs
    except Exception as e:
        log.debug("RSS probe failed for %s: %s", url, e)
    return None


def _fetch_html(url: str) -> dict:
    """Fetch HTML page, extract clean text, title, and metadata."""
    if not is_allowed_by_robots(url):
        return {"ok": False, "status": 403, "error": "Blocked by robots.txt", "docs": []}

    time.sleep(CRAWL_DELAY)

    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            },
            timeout=20,
            allow_redirects=True
        )

        http_status = resp.status_code
        if not resp.ok:
            return {
                "ok": False,
                "status": http_status,
                "error": f"HTTP {http_status}",
                "docs": []
            }

        html = resp.text
        # 1. Title extraction
        soup = BeautifulSoup(html[:10000], "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else ""

        # 2. Main content extraction via trafilatura
        body_text = trafilatura.extract(html) or ""
        if not body_text:
            # Fallback to paragraph extraction if trafilatura stripped too much
            paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
            body_text = "\n\n".join(paragraphs)

        if not body_text or len(body_text.strip()) < 40:
            return {
                "ok": True,
                "status": http_status,
                "error": "No meaningful text could be extracted from page",
                "docs": []
            }

        # 3. Publication date extraction from metadata
        pub_date = None
        try:
            meta = trafilatura.extract_metadata(html)
            if meta and meta.date:
                pub_date = _parse_published_date(meta.date)
        except Exception:
            pass

        content_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()

        return {
            "ok": True,
            "status": http_status,
            "error": None,
            "docs": [{
                "url": url,
                "title": title or "Web Page Document",
                "content": body_text,
                "content_hash": content_hash,
                "published_at": pub_date
            }]
        }
    except Exception as e:
        log.warning("Fetch failed for %s: %s", url, e)
        return {"ok": False, "status": None, "error": str(e), "docs": []}


def fetch(url: str) -> dict:
    """Convenience wrapper used during company site research."""
    res = _fetch_html(url)
    if res.get("ok") and res.get("docs"):
        doc = res["docs"][0]
        return {
            "ok": True,
            "status": res["status"],
            "text": doc["content"],
            "hash": doc["content_hash"]
        }
    return {
        "ok": res.get("ok", False),
        "status": res.get("status"),
        "error": res.get("error", "Failed to fetch page"),
        "text": ""
    }


def crawl_source(source_id: int) -> dict:
    """Crawl a single source, detect new/changed documents, log to crawl_runs."""
    source = query("SELECT * FROM sources WHERE id = %s", (source_id,), one=True)
    if not source:
        return {"ok": False, "error": "Source not found"}

    url = urllib.parse.unquote(source["url"])
    if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("internal://"):
        if url.startswith("www."):
            url = "https://" + url
        elif "://" in url:
            pass
        else:
            url = "https://" + url
    if url.startswith("internal://"):
        return {"ok": True, "skipped": True, "reason": "Internal source handled via upload endpoint"}

    # Probe RSS first, else fetch standard HTML
    rss_docs = _fetch_rss(url)
    if rss_docs:
        fetch_result = {
            "ok": True,
            "status": 200,
            "error": None,
            "docs": rss_docs
        }
    else:
        fetch_result = _fetch_html(url)

    http_status = fetch_result.get("status")
    error_msg = fetch_result.get("error")
    status_str = "success" if fetch_result.get("ok") else "failed"

    new_docs_count = 0
    with get_conn() as conn, conn.cursor() as cur:
        for doc in fetch_result.get("docs", []):
            try:
                # Deduplication: Insert only if (source_id, content_hash) does not exist
                cur.execute(
                    """INSERT INTO documents (
                         source_id, url, title, content, content_hash, published_at, discovered_at
                       ) VALUES (%s, %s, %s, %s, %s, %s, now())
                       ON CONFLICT (source_id, content_hash) DO NOTHING
                       RETURNING id""",
                    (
                        source_id,
                        doc["url"],
                        doc["title"][:255] if doc["title"] else None,
                        doc["content"],
                        doc["content_hash"],
                        doc["published_at"]
                    )
                )
                inserted = cur.fetchone()
                if inserted:
                    new_docs_count += 1
            except Exception as exc:
                log.warning("Failed to store document for source %s: %s", source_id, exc)

        # Log crawl run to crawl_runs table
        cur.execute(
            """INSERT INTO crawl_runs (
                 source_id, started_at, status, http_status, new_docs, error
               ) VALUES (%s, now(), %s, %s, %s, %s)""",
            (
                source_id,
                status_str,
                http_status,
                new_docs_count,
                error_msg
            )
        )

        # Update source metadata (last_checked, last_status_code)
        cur.execute(
            """UPDATE sources
               SET last_checked = now(),
                   last_status_code = %s
               WHERE id = %s""",
            (http_status, source_id)
        )

        conn.commit()

    return {
        "ok": fetch_result.get("ok"),
        "source_id": source_id,
        "url": url,
        "http_status": http_status,
        "new_docs": new_docs_count,
        "error": error_msg
    }


def crawl_company_sources(company_id: int) -> dict:
    """Crawl all approved sources for a company with error boundary."""
    approved_sources = query(
        """SELECT id, name, url, category
           FROM sources
           WHERE company_id = %s AND status = 'approved' AND url NOT LIKE 'internal://%%'
           ORDER BY id ASC""",
        (company_id,)
    ) or []

    results = []
    total_new_docs = 0
    success_count = 0
    failed_count = 0

    for s in approved_sources:
        try:
            res = crawl_source(s["id"])
            results.append({
                "source_id": s["id"],
                "name": s["name"],
                "url": s["url"],
                "category": s["category"],
                **res
            })
            if res.get("ok"):
                success_count += 1
                total_new_docs += res.get("new_docs", 0)
            else:
                failed_count += 1
        except Exception as e:
            log.error("Unhandled error crawling source %s (%s): %s", s["id"], s["url"], e)
            failed_count += 1
            results.append({
                "source_id": s["id"],
                "name": s["name"],
                "url": s["url"],
                "ok": False,
                "error": str(e)
            })

    return {
        "company_id": company_id,
        "total_sources": len(approved_sources),
        "successful_crawls": success_count,
        "failed_crawls": failed_count,
        "new_documents_collected": total_new_docs,
        "results": results
    }
