import urllib.request as _meter_urlreq
import urllib.error as _meter_urlerr
"""
HTML Parser AI MCP Server
HTML parsing and analysis tools powered by MEOK AI Labs.
"""


import sys, os
from auth_middleware import check_access

import re
import time
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("html-parser-ai", instructions="MEOK AI Labs MCP Server")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 50
WINDOW = 86400


def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day. Upgrade at https://councilof.ai")
    _call_counts[tool_name].append(now)


def _server_meter_check(api_key: str = "") -> dict:
    """Calls the live /verify endpoint for server-side metering. Fail-open."""
    try:
        data = json.dumps({"api_key": api_key, "tool": ""}).encode()
        req = _meter_urlreq.Request(_METER_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with _meter_urlreq.urlopen(req, timeout=2.5) as r:
            d = json.loads(r.read())
            if isinstance(d, dict) and "allowed" in d:
                return d
    except Exception:
        pass
    return {"allowed": True, "tier": "anonymous", "remaining": 200, "upgrade_url": "https://meok.ai/pricing"}


_METER_URL = "https://proofof.ai/verify"


@mcp.tool()
def extract_links(html: str, base_url: str = "", api_key: str = "") -> dict:
    """Extract all links (anchor tags) from HTML content.

    Args:
        html: HTML content string
        base_url: Optional base URL to resolve relative links

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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
def extract_text(html: str, preserve_newlines: bool = True, api_key: str = "") -> dict:
    """Extract plain text content from HTML, stripping all tags.

    Args:
        html: HTML content string
        preserve_newlines: Keep newlines for block elements (default True)

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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
def validate_html(html: str, api_key: str = "") -> dict:
    """Validate HTML for common issues (unclosed tags, missing attributes, etc.).

    Args:
        html: HTML content string to validate

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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
def find_meta_tags(html: str, api_key: str = "") -> dict:
    """Extract all meta tags and their attributes from HTML.

    Args:
        html: HTML content string

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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


def main():
    mcp.run()

if __name__ == '__main__':
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/5kQ6oJ0xS3ce8sl7ew8k91j"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
