# Question Bank MCP Server

An MCP (Model Context Protocol) server that helps teachers create, manage, and organize test questions with Claude's assistance.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MCP](https://img.shields.io/badge/MCP-1.26-green)
![Claude](https://img.shields.io/badge/Claude-Desktop-blueviolet)

## What It Does

Claude becomes a teaching assistant for assessment creation:

- **Create questions** with difficulty ratings, Bloom's taxonomy levels, and topic tags
- **Organize question banks** by course, subject, and grade level
- **Search and filter** questions by any criteria
- **Get suggestions** for new questions based on learning objectives
- **Track statistics** on question distribution and coverage

## Demo

Ask Claude things like:

- "Create a question bank for Biology 101"
- "Add a topic for Photosynthesis"
- "Create a multiple choice question about cellular respiration"
- "Show me all hard questions in the Analyze level"
- "What are the statistics for my question bank?"
- "Suggest 5 questions about mitosis"

## Tools

| Tool | Description |
|------|-------------|
| `create_question_bank` | Create a new question bank for a course |
| `list_question_banks` | List all question banks |
| `get_bank_statistics` | Get detailed stats (difficulty distribution, Bloom's coverage) |
| `create_topic` | Add a topic to organize questions |
| `list_topics` | List topics in a question bank |
| `create_question` | Create a new question with full metadata |
| `get_question` | Retrieve a question by ID |
| `update_question` | Modify an existing question |
| `delete_question` | Remove a question |
| `search_questions` | Search with filters (topic, difficulty, Bloom's, tags) |
| `activate_questions` | Change questions from draft to active status |
| `suggest_questions` | Get AI suggestions for questions to create |

## Question Metadata

Each question includes:

| Field | Description |
|-------|-------------|
| `question_type` | multiple_choice, true_false, short_answer, essay |
| `difficulty` | 0.0 (easy) to 1.0 (hard) |
| `bloom_level` | remember, understand, apply, analyze, evaluate, create |
| `topics` | Linked topics for organization |
| `tags` | Flexible tagging |
| `points` | Point value |
| `estimated_time_seconds` | Expected time to answer |
| `explanation` | Why the answer is correct |

## Resources

| Resource | Description |
|----------|-------------|
| `questionbank://blooms-taxonomy` | Bloom's Taxonomy reference |
| `questionbank://question-types` | Question type guide |

## Setup

### 1. Clone and Install
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

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. The question bank tools will be available.

## Project Structure
```
question-bank-mcp/
├── run_server.py              # MCP server entry point
├── src/
│   └── question_bank/
│       ├── server.py          # MCP tools and resources
│       └── database.py        # SQLite database
├── data/
│   └── question_bank.db       # SQLite database (auto-created)
└── requirements.txt
```

## Use Cases

### For Teachers
- Build question banks for courses
- Ensure coverage across Bloom's taxonomy levels
- Balance difficulty across assessments
- Reuse questions across semesters

### For Curriculum Designers
- Create standardized question templates
- Maintain consistent difficulty calibration
- Organize questions by learning objectives

### For Ed-Tech Platforms
- Foundation for adaptive testing systems
- Question metadata for IRT algorithms
- Topic tagging for learning analytics

## Bloom's Taxonomy Quick Reference

| Level | Description | Example Verbs |
|-------|-------------|---------------|
| Remember | Recall facts | define, list, name |
| Understand | Explain ideas | describe, explain, summarize |
| Apply | Use in new situations | solve, calculate, demonstrate |
| Analyze | Draw connections | compare, contrast, examine |
| Evaluate | Justify decisions | evaluate, judge, critique |
| Create | Produce new work | design, construct, develop |

## License

MIT

---

Built by [Jim Williams](https://linkedin.com/in/woodstocksoftware) | [GitHub](https://github.com/woodstocksoftware)
