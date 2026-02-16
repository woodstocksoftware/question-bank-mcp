#!/usr/bin/env python
"""Run the Question Bank MCP server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.question_bank.server import mcp
mcp.run(transport="stdio")
