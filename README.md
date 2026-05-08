<div align="center">

# Html Parser Ai MCP

**HTML Parser AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-html-parser-ai-mcp)](https://pypi.org/project/meok-html-parser-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

HTML Parser AI MCP Server
HTML parsing and analysis tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `extract_links` | Extract all links (anchor tags) from HTML content. |
| `extract_text` | Extract plain text content from HTML, stripping all tags. |
| `validate_html` | Validate HTML for common issues (unclosed tags, missing attributes, etc.). |
| `find_meta_tags` | Extract all meta tags and their attributes from HTML. |

## Installation

```bash
pip install meok-html-parser-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "html-parser-ai": {
      "command": "python",
      "args": ["-m", "meok_html_parser_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
