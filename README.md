# Question Bank MCP Server

An MCP server for managing K-12 assessment question banks with IRT metadata. Build, organize, and search test questions with full Bloom's taxonomy classification, difficulty calibration, and topic tagging — all through natural language with Claude.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MCP](https://img.shields.io/badge/MCP-1.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io) (MCP) is an open standard that lets AI assistants like Claude connect to external tools and data sources. This server gives Claude the ability to create, manage, and query question banks directly — no copy-pasting or manual data entry.

## Features

- **Question CRUD** — Create, read, update, and delete questions with full metadata
- **Question types** — Multiple choice, true/false, short answer, and essay
- **Bloom's taxonomy** — Classify questions across all 6 cognitive levels (remember through create)
- **Difficulty calibration** — Continuous 0.0–1.0 scale with easy/medium/hard bucketing
- **IRT metadata** — `discrimination_index`, `times_used`, `times_correct`, `avg_time_seconds`
- **Topic hierarchy** — Organize questions into nested topics within banks
- **Flexible tagging** — Tag questions with arbitrary labels for cross-cutting categorization
- **Search and filter** — Query by type, difficulty range, Bloom's level, topic, tags, status, or free text
- **Bulk activation** — Move multiple questions from draft to active in one call
- **AI suggestions** — Get question ideas for a topic at specified difficulty and Bloom's levels
- **Bank statistics** — Detailed breakdowns by type, difficulty, Bloom's level, and topic

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/woodstocksoftware/question-bank-mcp.git
cd question-bank-mcp
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

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

Then restart Claude Desktop.

### 3. Configure Claude Code

```bash
claude mcp add question-bank /path/to/question-bank-mcp/venv/bin/python /path/to/question-bank-mcp/run_server.py
```

### 4. Start using it

Ask Claude things like:

> "Create a question bank for AP Biology"
>
> "Add a topic for Cellular Respiration"
>
> "Create a multiple choice question about the Krebs cycle at the Analyze level"
>
> "Show me all hard questions tagged as 'midterm'"
>
> "What are the statistics for my question bank?"

## Tool Reference

### Question Bank Tools

#### `create_question_bank`

Create a new question bank for a course or subject area.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | yes | Name of the question bank |
| `subject` | string | yes | Subject area (e.g., "Biology", "Algebra") |
| `description` | string | no | Description of the bank |
| `grade_level` | string | no | Target grade level (e.g., "9-12", "AP") |

#### `list_question_banks`

List all question banks with their question and topic counts. No parameters.

#### `get_bank_statistics`

Get detailed statistics for a question bank, including breakdowns by question type, difficulty bucket, Bloom's level, and topic.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | yes | The question bank ID |

### Topic Tools

#### `create_topic`

Add a topic to organize questions within a bank. Supports hierarchical nesting via `parent_topic_id`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | yes | The question bank ID |
| `name` | string | yes | Topic name |
| `description` | string | no | Topic description |
| `parent_topic_id` | string | no | Parent topic ID for nesting |

#### `list_topics`

List all topics in a question bank with question counts.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | yes | The question bank ID |

### Question Tools

#### `create_question`

Create a new question with full metadata. Questions start in `draft` status.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bank_id` | string | yes | — | The question bank ID |
| `question_type` | string | yes | — | `multiple_choice`, `true_false`, `short_answer`, or `essay` |
| `stem` | string | yes | — | The question text |
| `correct_answer` | string | yes | — | Correct answer or rubric |
| `options` | list | no | — | Answer choices (for multiple choice) |
| `explanation` | string | no | — | Why the answer is correct |
| `difficulty` | float | no | `0.5` | 0.0 (easy) to 1.0 (hard) |
| `bloom_level` | string | no | — | Bloom's taxonomy level |
| `estimated_time_seconds` | int | no | `60` | Expected time to answer |
| `points` | int | no | `1` | Point value |
| `topic_ids` | list | no | — | Topic IDs to link |
| `tags` | list | no | — | Categorization tags |

#### `get_question`

Retrieve a question by ID with all metadata.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question_id` | string | yes | — | The question ID |
| `show_answer` | bool | no | `true` | Whether to include the answer |

#### `update_question`

Update any field on an existing question, including changing its status.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question_id` | string | yes | The question ID |
| *(any question field)* | — | no | Fields to update |

#### `delete_question`

Permanently delete a question.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question_id` | string | yes | The question ID |

#### `search_questions`

Search and filter questions across banks with multiple criteria.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bank_id` | string | no | — | Filter by bank |
| `topic_id` | string | no | — | Filter by topic |
| `question_type` | string | no | — | Filter by type |
| `bloom_level` | string | no | — | Filter by Bloom's level |
| `difficulty_min` | float | no | — | Minimum difficulty |
| `difficulty_max` | float | no | — | Maximum difficulty |
| `status` | string | no | — | `draft`, `active`, or `archived` |
| `tags` | list | no | — | Filter by tags (any match) |
| `search_text` | string | no | — | Text search in stem and explanation |
| `limit` | int | no | `20` | Maximum results |

#### `activate_questions`

Bulk-activate questions, moving them from `draft` to `active` status.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question_ids` | list | yes | List of question IDs to activate |

#### `suggest_questions`

Get AI-friendly suggestions for new questions to create, based on topic and constraints.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bank_id` | string | yes | — | The question bank ID |
| `topic` | string | yes | — | Topic or learning objective |
| `count` | int | no | `5` | Number of suggestions |
| `difficulty` | string | no | `"mixed"` | `easy`, `medium`, `hard`, or `mixed` |
| `bloom_levels` | list | no | all | Bloom's levels to target |

## Resources

| URI | Description |
|-----|-------------|
| `questionbank://blooms-taxonomy` | Bloom's Taxonomy reference — 6 levels with action verbs, example questions, and writing tips |
| `questionbank://question-types` | Question type guide — when to use each type, best practices |

## Question Schema

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | auto | UUID with `q-` prefix |
| `bank_id` | string | — | Parent question bank |
| `question_type` | enum | — | `multiple_choice`, `true_false`, `short_answer`, `essay` |
| `stem` | string | — | The question text |
| `options` | list | — | Answer choices (multiple choice only) |
| `correct_answer` | string | — | Answer or rubric |
| `explanation` | string | — | Why the answer is correct |
| `difficulty` | float | `0.5` | 0.0 (easy) to 1.0 (hard) |
| `bloom_level` | enum | — | `remember`, `understand`, `apply`, `analyze`, `evaluate`, `create` |
| `estimated_time_seconds` | int | `60` | Expected answer time |
| `points` | int | `1` | Point value |
| `status` | enum | `draft` | `draft`, `active`, `archived` |
| `times_used` | int | `0` | Usage counter |
| `times_correct` | int | `0` | Correct response counter |
| `avg_time_seconds` | float | — | Average response time |
| `discrimination_index` | float | — | IRT discrimination parameter |
| `created_at` | timestamp | now | Creation time |
| `updated_at` | timestamp | now | Last update time |

### Difficulty Buckets

| Bucket | Range | Description |
|--------|-------|-------------|
| Easy | 0.0 – 0.3 | Recall and basic comprehension |
| Medium | 0.3 – 0.7 | Application and analysis |
| Hard | 0.7 – 1.0 | Evaluation and synthesis |

### Bloom's Taxonomy Levels

| Level | Example Verbs |
|-------|---------------|
| Remember | define, list, name, identify, recall |
| Understand | describe, explain, summarize, interpret |
| Apply | solve, use, demonstrate, calculate |
| Analyze | compare, contrast, examine, differentiate |
| Evaluate | evaluate, judge, critique, defend |
| Create | design, construct, develop, formulate |

## Usage Examples

### Build a math question bank

> "Create a question bank called 'Algebra 2' for grades 10-11"
>
> "Add topics for Polynomials, Quadratic Equations, and Exponential Functions"
>
> "Create 3 multiple choice questions about factoring polynomials at the Apply level, difficulty 0.4–0.6"
>
> "Activate all the questions we just created"

### Search by difficulty and Bloom's level

> "Find all hard questions at the Evaluate or Create level"
>
> "Search for questions about quadratics with difficulty above 0.7"
>
> "Show me all draft questions tagged 'final-exam'"

### Get suggestions for gaps

> "What are the statistics for my Algebra 2 bank?"
>
> "Suggest 5 easy Remember-level questions about exponential growth"
>
> "We need more Analyze-level questions — suggest some for Quadratic Equations"

## Architecture

```
┌─────────────────────────────────────────────┐
│             Claude Desktop / Code            │
│               (MCP Client)                   │
└──────────────────┬──────────────────────────┘
                   │ stdio
┌──────────────────▼──────────────────────────┐
│  run_server.py                               │
│  └─ src/question_bank/server.py              │
│     ├─ 12 tools  (@mcp.tool)                │
│     ├─ 2 resources (@mcp.resource)           │
│     └─ Markdown-formatted responses          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  src/question_bank/database.py               │
│  ├─ question_banks     (top-level containers)│
│  ├─ topics             (hierarchical)        │
│  ├─ questions          (content + IRT)       │
│  ├─ question_topics    (many-to-many)        │
│  └─ question_tags      (many-to-many)        │
└──────────────────┬──────────────────────────┘
                   │
              data/question_bank.db (SQLite)
```

## QTI 3.0 Compatibility

The question schema is designed with [QTI 3.0](https://www.imsglobal.org/question/index.html) compatibility in mind. The data model supports the core fields needed for QTI export (question types, correct answers, options, metadata), but import/export is not yet implemented. This is a planned future enhancement.

## Testing

No automated test suite yet. To verify the database layer works correctly:

```bash
python -m src.question_bank.database
```

To confirm the server starts:

```bash
python run_server.py
```

The server runs on stdio transport, so it will appear to hang (it's waiting for MCP client input). Press `Ctrl+C` to stop.

## Contributing

Contributions are welcome! This project is in early development. Areas that could use help:

- Automated tests (pytest)
- QTI 3.0 import/export
- Additional question types
- CI/CD pipeline

## License

[MIT](LICENSE)

---

Built by [Jim Williams](https://linkedin.com/in/woodstocksoftware) | [GitHub](https://github.com/woodstocksoftware)
