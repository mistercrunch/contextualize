---
name: mcp
references: [core, python]
---

# MCP (Model Context Protocol) Concepts

## Overview

MCP allows Claude Code to communicate with external servers that provide tools and context.

## Structure

- **Tools**: Functions that can be called with parameters
- **Input Schema**: JSON schema defining tool parameters
- **Output Format**: Structured responses with content/error

## Implementation

- Use `@tool` decorator to define tools
- Async functions for non-blocking operations
- Return dict with `content` array
- Set `is_error: True` for failures

## Configuration

```json
{
  "name": "server-name",
  "command": "python3",
  "args": ["server.py"],
  "tools": {...}
}
```

## Usage

`claude --mcp-config config.json`
