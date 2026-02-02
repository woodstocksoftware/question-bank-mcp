#!/usr/bin/env python
"""Run the Question Bank MCP server."""
import sys
sys.path.insert(0, '/Users/james/projects/question-bank-mcp')

from src.question_bank.server import mcp
mcp.run(transport="stdio")
