"""
HTML Parser AI MCP Server
HTML parsing and analysis tools powered by MEOK AI Labs.
"""

import re
import time
from collections import defaultdict
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


@mcp.tool()
def extract_links(html: str, base_url: str = "") -> dict:
    """Extract all links (anchor tags) from HTML content.

    Args:
        html: HTML content string
        base_url: Optional base URL to resolve relative links
    """
    _check_rate_limit("extract_links")
    links = []
    for match in re.finditer(r'<a\s[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
        href, text = match.group(1), re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if base_url and not href.startswith(('http://', 'https://', 'mailto:', '#', 'javascript:')):
            href = base_url.rstrip('/') + '/' + href.lstrip('/')
        links.append({"href": href, "text": text[:100]})
    internal = [l for l in links if base_url and l["href"].startswith(base_url)]
    external = [l for l in links if l["href"].startswith(('http://', 'https://')) and l not in internal]
    return {"links": links, "total": len(links), "internal": len(internal), "external": len(external)}


@mcp.tool()
def extract_text(html: str, preserve_newlines: bool = True) -> dict:
    """Extract plain text content from HTML, stripping all tags.

    Args:
        html: HTML content string
        preserve_newlines: Keep newlines for block elements (default True)
    """
    _check_rate_limit("extract_text")
    text = html
    if preserve_newlines:
        for tag in ('</p>', '</div>', '</h1>', '</h2>', '</h3>', '</h4>', '</h5>', '</h6>',
                     '<br>', '<br/>', '<br />', '</li>', '</tr>'):
            text = text.replace(tag, tag + '\n')
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    if preserve_newlines:
        text = re.sub(r'\n{3,}', '\n\n', text)
    else:
        text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    words = text.split()
    return {"text": text, "length": len(text), "word_count": len(words)}


@mcp.tool()
def validate_html(html: str) -> dict:
    """Validate HTML for common issues (unclosed tags, missing attributes, etc.).

    Args:
        html: HTML content string to validate
    """
    _check_rate_limit("validate_html")
    issues = []
    void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                     'link', 'meta', 'param', 'source', 'track', 'wbr'}
    open_tags = []
    for match in re.finditer(r'<(/?)(\w+)([^>]*)/?>', html):
        is_close, tag, attrs = match.group(1), match.group(2).lower(), match.group(3)
        if is_close:
            if tag in void_elements:
                issues.append({"issue": f"Unnecessary closing tag for void element </{tag}>", "severity": "warning"})
            elif open_tags and open_tags[-1] == tag:
                open_tags.pop()
            elif tag in open_tags:
                issues.append({"issue": f"Misnested closing tag </{tag}>", "severity": "error"})
                open_tags.remove(tag)
            else:
                issues.append({"issue": f"Closing tag </{tag}> without matching open tag", "severity": "error"})
        elif tag not in void_elements and not match.group(0).endswith('/>'):
            open_tags.append(tag)
    for tag in open_tags:
        issues.append({"issue": f"Unclosed tag <{tag}>", "severity": "error"})
    for match in re.finditer(r'<img\s[^>]*>', html, re.IGNORECASE):
        if 'alt=' not in match.group(0).lower():
            issues.append({"issue": "Image missing alt attribute", "severity": "warning"})
    if not re.search(r'<!DOCTYPE', html, re.IGNORECASE):
        issues.append({"issue": "Missing DOCTYPE declaration", "severity": "info"})
    errors = sum(1 for i in issues if i["severity"] == "error")
    return {"valid": errors == 0, "issues": issues, "error_count": errors,
            "warning_count": sum(1 for i in issues if i["severity"] == "warning")}


@mcp.tool()
def find_meta_tags(html: str) -> dict:
    """Extract all meta tags and their attributes from HTML.

    Args:
        html: HTML content string
    """
    _check_rate_limit("find_meta_tags")
    metas = []
    for match in re.finditer(r'<meta\s([^>]+?)/?>', html, re.IGNORECASE):
        attrs = {}
        for attr in re.finditer(r'(\w[\w-]*)=["\']([^"\']*)["\']', match.group(1)):
            attrs[attr.group(1).lower()] = attr.group(2)
        metas.append(attrs)
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else None
    og_tags = {m.get("property", ""): m.get("content", "") for m in metas if m.get("property", "").startswith("og:")}
    twitter_tags = {m.get("name", ""): m.get("content", "") for m in metas if m.get("name", "").startswith("twitter:")}
    charset = next((m.get("charset", m.get("content", "")) for m in metas if "charset" in m), None)
    return {"title": title, "meta_tags": metas, "total": len(metas),
            "open_graph": og_tags, "twitter_cards": twitter_tags, "charset": charset}


if __name__ == "__main__":
    mcp.run()
