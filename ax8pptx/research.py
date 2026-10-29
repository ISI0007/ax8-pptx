"""Research crawl - fills the 'sources' fields with real, fetched citations.

No API key needed: it crawls a seed set of pages, extracts title + snippet,
scores by keyword overlap with the slide intent, and returns the top hits
with their URLs. The LLM then cites from this list only.
"""

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Iterable, List

UA = "AX8-PPTX/0.1 (+research)"
STOP = set("""a an the of and or to in on for with by is are was were be been
this that these those from as at it its""".split())


@dataclass
class Source:
    title: str
    url: str
    snippet: str
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _fetch(url: str, timeout: int = 20, limit: int = 400_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(limit)
    charset = r.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, "replace")


def _text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;?", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def _title(html: str, fallback: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    return _text(m.group(1))[:120] if m else fallback


def _terms(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{3,}", s.lower()) if w not in STOP}


def crawl(seeds: Iterable[str], query: str, top: int = 8) -> List[Source]:
    """Fetch each seed, score against the query, return ranked sources."""
    qterms = _terms(query)
    out: List[Source] = []
    for url in seeds:
        try:
            html = _fetch(url)
        except Exception as e:  # network/parse failures must not kill the deck
            out.append(Source(title=f"[unreachable] {url}", url=url,
                              snippet=f"{type(e).__name__}", score=-1))
            continue
        body = _text(html)
        title = _title(html, url)
        overlap = len(qterms & _terms(title + " " + body[:4000]))
        dens = overlap / max(1, len(qterms))
        snippet = body[:240]
        out.append(Source(title=title, url=url, snippet=snippet, score=round(dens, 3)))
    out.sort(key=lambda s: s.score, reverse=True)
    return out[:top]


def citation_block(sources: List[Source]) -> str:
    """Compact block injected into the generation prompt."""
    lines = []
    for i, s in enumerate(sources, 1):
        lines.append(f"[{i}] {s.title} - {s.url}")
        lines.append(f"    {s.snippet}")
    return "\n".join(lines)


def search_urls(query: str, engine: str = "duckduckgo") -> List[str]:
    """Best-effort SERP scrape. Returns candidate URLs (may be empty)."""
    q = urllib.parse.quote_plus(query)
    if engine == "duckduckgo":
        url = f"https://lite.duckduckgo.com/lite/?q={q}"
        link_re = r'href="(https?://(?!duckduckgo\.com)[^"]+)"'
    else:
        url = f"https://www.bing.com/search?q={q}"
        link_re = r'href="(https?://(?!www\.bing\.com)[^"]+)"'
    try:
        html = _fetch(url)
    except Exception:
        return []
    seen, urls = set(), []
    for m in re.findall(link_re, html):
        u = urllib.parse.unquote(m)
        host = urllib.parse.urlparse(u).netloc
        if host in seen:
            continue
        seen.add(host)
        urls.append(u)
        if len(urls) >= 10:
            break
    return urls
