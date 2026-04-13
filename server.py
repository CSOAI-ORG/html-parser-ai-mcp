"""
HTML Parser AI MCP Server
HTML parsing and extraction tools powered by MEOK AI Labs.
"""

import re
import time
from collections import defaultdict
from html.parser import HTMLParser
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("html-parser-ai-mcp")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 50
WINDOW = 86400

def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day. Upgrade at https://meok.ai/pricing")
    _call_counts[tool_name].append(now)


class _LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            text = dict(attrs).get('title', '')
            if href:
                self.links.append({"href": href, "title": text})


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self._skip = True
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self._skip = False
        if tag in ('p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr'):
            self.text_parts.append('\n')
    def handle_data(self, data):
        if not self._skip:
            self.text_parts.append(data)


class _MetaExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta_tags = []
        self.title = ""
        self._in_title = False
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            self.meta_tags.append(dict(attrs))
        if tag == 'title':
            self._in_title = True
    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
    def handle_data(self, data):
        if self._in_title:
            self.title += data


@mcp.tool()
def extract_links(html: str, base_url: str = "") -> dict:
    """Extract all links from HTML content.

    Args:
        html: HTML string to parse
        base_url: Base URL to resolve relative links
    """
    _check_rate_limit("extract_links")
    parser = _LinkExtractor()
    parser.feed(html)
    links = parser.links
    if base_url:
        for link in links:
            href = link["href"]
            if href.startswith('/'):
                link["href"] = base_url.rstrip('/') + href
                link["resolved"] = True
    internal = [l for l in links if base_url and l["href"].startswith(base_url)]
    external = [l for l in links if base_url and not l["href"].startswith(base_url)]
    return {"links": links[:200], "total": len(links),
            "internal_count": len(internal) if base_url else 0,
            "external_count": len(external) if base_url else 0}


@mcp.tool()
def extract_text(html: str) -> dict:
    """Extract visible text content from HTML, stripping all tags.

    Args:
        html: HTML string to extract text from
    """
    _check_rate_limit("extract_text")
    parser = _TextExtractor()
    parser.feed(html)
    raw = ''.join(parser.text_parts)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', raw)
    text = re.sub(r'[ \t]+', ' ', text).strip()
    words = text.split()
    return {"text": text[:10000], "word_count": len(words), "char_count": len(text),
            "truncated": len(text) > 10000}


@mcp.tool()
def validate_html(html: str) -> dict:
    """Validate HTML for common issues (unclosed tags, nesting errors).

    Args:
        html: HTML string to validate
    """
    _check_rate_limit("validate_html")
    issues = []
    self_closing = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
    stack = []
    tag_pattern = re.compile(r'<(/?)(\w+)([^>]*?)(/?)>')
    for m in tag_pattern.finditer(html):
        is_close, tag, attrs, self_close = m.groups()
        tag = tag.lower()
        if tag in self_closing:
            continue
        if self_close:
            continue
        if is_close:
            if not stack:
                issues.append({"type": "error", "message": f"Unexpected closing tag </{tag}>", "position": m.start()})
            elif stack[-1] != tag:
                issues.append({"type": "error", "message": f"Mismatched tag: expected </{stack[-1]}>, found </{tag}>", "position": m.start()})
                if tag in stack:
                    while stack and stack[-1] != tag:
                        stack.pop()
                    if stack:
                        stack.pop()
            else:
                stack.pop()
        else:
            stack.append(tag)
    for tag in stack:
        issues.append({"type": "error", "message": f"Unclosed tag <{tag}>"})
    if not re.search(r'<!DOCTYPE', html, re.IGNORECASE):
        issues.append({"type": "warning", "message": "Missing DOCTYPE declaration"})
    if not re.search(r'<html', html, re.IGNORECASE):
        issues.append({"type": "warning", "message": "Missing <html> tag"})
    score = max(0, 100 - len([i for i in issues if i["type"] == "error"]) * 15 - len([i for i in issues if i["type"] == "warning"]) * 5)
    return {"valid": len([i for i in issues if i["type"] == "error"]) == 0, "issues": issues[:50],
            "issue_count": len(issues), "score": score}


@mcp.tool()
def find_meta_tags(html: str) -> dict:
    """Extract all meta tags and title from HTML.

    Args:
        html: HTML string to parse
    """
    _check_rate_limit("find_meta_tags")
    parser = _MetaExtractor()
    parser.feed(html)
    og_tags = {t.get("property", ""): t.get("content", "") for t in parser.meta_tags if t.get("property", "").startswith("og:")}
    twitter_tags = {t.get("name", ""): t.get("content", "") for t in parser.meta_tags if t.get("name", "").startswith("twitter:")}
    description = next((t.get("content", "") for t in parser.meta_tags if t.get("name", "").lower() == "description"), "")
    keywords = next((t.get("content", "") for t in parser.meta_tags if t.get("name", "").lower() == "keywords"), "")
    return {"title": parser.title.strip(), "description": description, "keywords": keywords,
            "og_tags": og_tags, "twitter_tags": twitter_tags, "all_meta": parser.meta_tags[:30],
            "meta_count": len(parser.meta_tags)}


if __name__ == "__main__":
    mcp.run()
