# Html Parser Ai

> By [MEOK AI Labs](https://meok.ai) — MEOK AI Labs MCP Server

HTML Parser AI MCP Server

## Installation

```bash
pip install html-parser-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install html-parser-ai-mcp
```

## Tools

### `extract_links`
Extract all links (anchor tags) from HTML content.

**Parameters:**
- `html` (str)
- `base_url` (str)

### `extract_text`
Extract plain text content from HTML, stripping all tags.

**Parameters:**
- `html` (str)
- `preserve_newlines` (bool)

### `validate_html`
Validate HTML for common issues (unclosed tags, missing attributes, etc.).

**Parameters:**
- `html` (str)

### `find_meta_tags`
Extract all meta tags and their attributes from HTML.

**Parameters:**
- `html` (str)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/html-parser-ai-mcp](https://github.com/CSOAI-ORG/html-parser-ai-mcp)
- **PyPI**: [pypi.org/project/html-parser-ai-mcp](https://pypi.org/project/html-parser-ai-mcp/)

## License

MIT — MEOK AI Labs
