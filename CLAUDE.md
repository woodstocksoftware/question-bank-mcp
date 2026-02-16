# CLAUDE.md — Question Bank MCP Server

## Tech Stack

- **Language:** Python 3.12
- **Framework:** FastMCP (`mcp>=1.0.0`)
- **Database:** SQLite (auto-created at `data/question_bank.db`)
- **Transport:** stdio
- **Dependencies:** `mcp>=1.0.0`, `python-dateutil>=2.8.0`

## How to Run

```bash
# From project root (with venv activated)
python run_server.py

# Or as a module
python -m src.question_bank
```

## How to Connect

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "question-bank": {
      "command": "/path/to/question-bank-mcp/venv/bin/python",
      "args": ["/path/to/question-bank-mcp/run_server.py"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add question-bank /path/to/question-bank-mcp/venv/bin/python /path/to/question-bank-mcp/run_server.py
```

## Architecture

```
run_server.py                  # Entry point — imports mcp from server.py, runs stdio
src/question_bank/
├── __init__.py
├── __main__.py                # python -m entry point
├── server.py                  # 12 MCP tools + 2 MCP resources (~800 lines)
└── database.py                # SQLite ORM layer (~500 lines)
data/
└── question_bank.db           # SQLite database (auto-created, gitignored)
```

- `server.py` defines all tools and resources using the `@mcp.tool()` and `@mcp.resource()` decorators
- `database.py` handles all SQL — table creation, CRUD, search queries
- The database auto-initializes on first import (creates tables + indexes)

## Tools (12)

| Tool | Key Parameters |
|------|---------------|
| `create_question_bank` | `name`, `subject`, `description?`, `grade_level?` |
| `list_question_banks` | *(none)* |
| `get_bank_statistics` | `bank_id` |
| `create_topic` | `bank_id`, `name`, `description?`, `parent_topic_id?` |
| `list_topics` | `bank_id` |
| `create_question` | `bank_id`, `question_type`, `stem`, `correct_answer`, `options?`, `explanation?`, `difficulty?`, `bloom_level?`, `estimated_time_seconds?`, `points?`, `topic_ids?`, `tags?` |
| `get_question` | `question_id`, `show_answer?` |
| `update_question` | `question_id`, plus any question field |
| `delete_question` | `question_id` |
| `search_questions` | `bank_id?`, `topic_id?`, `question_type?`, `bloom_level?`, `difficulty_min?`, `difficulty_max?`, `status?`, `tags?`, `search_text?`, `limit?` |
| `activate_questions` | `question_ids` (list) |
| `suggest_questions` | `bank_id`, `topic`, `count?`, `difficulty?`, `bloom_levels?` |

## Resources (2)

| URI | Description |
|-----|-------------|
| `questionbank://blooms-taxonomy` | Bloom's Taxonomy reference with levels, verbs, and tips |
| `questionbank://question-types` | Question type guide (MC, T/F, short answer, essay) |

## Question Schema

### Enums

- **`question_type`:** `multiple_choice`, `true_false`, `short_answer`, `essay`
- **`bloom_level`:** `remember`, `understand`, `apply`, `analyze`, `evaluate`, `create`
- **`status`:** `draft`, `active`, `archived`

### Difficulty Model

- Float range `0.0` (easy) to `1.0` (hard), default `0.5`
- Buckets: easy (< 0.3), medium (0.3–0.7), hard (> 0.7)

### IRT / Usage Fields

- `times_used`, `times_correct` — usage counters
- `avg_time_seconds` — average response time
- `discrimination_index` — IRT discrimination parameter

## Database Tables

| Table | Purpose |
|-------|---------|
| `question_banks` | Top-level containers (id, name, subject, grade_level) |
| `topics` | Hierarchical topics within banks (supports parent_id) |
| `questions` | All question data, metadata, and IRT fields |
| `question_topics` | Many-to-many: questions ↔ topics |
| `question_tags` | Many-to-many: questions ↔ tags |

## Key Conventions

- **IDs:** UUID hex with prefixes — `bank-{8hex}`, `topic-{8hex}`, `q-{8hex}`
- **Tool output:** Markdown-formatted strings (headers, tables, bold labels)
- **Lifecycle:** `draft` → `active` → `archived` (new questions default to `draft`)
- **Foreign keys:** Enabled via `PRAGMA foreign_keys = ON`
- **Options field:** JSON-serialized list for multiple choice answers
- **Search:** `search_text` does LIKE matching against `stem` and `explanation`
