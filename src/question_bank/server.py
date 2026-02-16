"""
Question Bank MCP Server

Helps teachers create, manage, and organize test questions with:
- Difficulty ratings
- Bloom's taxonomy classification
- Topic tagging
- Question bank organization
"""

import json
import uuid
from mcp.server.fastmcp import FastMCP
from . import database as db

# Initialize MCP server
mcp = FastMCP("Question Bank")


# ============================================================
# QUESTION BANK TOOLS
# ============================================================

@mcp.tool()
def create_question_bank(
    name: str,
    subject: str,
    description: str = None,
    grade_level: str = None
) -> str:
    """
    Create a new question bank for organizing questions.
    
    Args:
        name: Name of the question bank (e.g., "Algebra I Midterm")
        subject: Subject area (e.g., "Mathematics", "Science", "English")
        description: Optional description of the question bank
        grade_level: Target grade level (e.g., "9th Grade", "College")
    
    Returns:
        Confirmation with bank details
    """
    bank_id = f"bank-{uuid.uuid4().hex[:8]}"
    
    bank = db.create_question_bank(
        bank_id=bank_id,
        name=name,
        subject=subject,
        description=description,
        grade_level=grade_level
    )
    
    return f"""
✅ Question Bank Created!

**ID:** {bank['id']}
**Name:** {bank['name']}
**Subject:** {bank['subject']}
**Grade Level:** {bank['grade_level'] or 'Not specified'}
**Description:** {bank['description'] or 'None'}

Next steps:
- Add topics with `create_topic`
- Add questions with `create_question`
"""


@mcp.tool()
def list_question_banks() -> str:
    """
    List all question banks.
    
    Returns:
        List of question banks with question counts
    """
    banks = db.list_question_banks()
    
    if not banks:
        return "No question banks found. Create one with `create_question_bank`."
    
    result = "**Question Banks:**\n\n"
    
    for bank in banks:
        result += f"### {bank['name']}\n"
        result += f"- **ID:** `{bank['id']}`\n"
        result += f"- **Subject:** {bank['subject']}\n"
        result += f"- **Grade Level:** {bank['grade_level'] or 'Not specified'}\n"
        result += f"- **Questions:** {bank['question_count']} | **Topics:** {bank['topic_count']}\n\n"
    
    return result


@mcp.tool()
def get_bank_statistics(bank_id: str) -> str:
    """
    Get detailed statistics for a question bank.
    
    Args:
        bank_id: The question bank ID
    
    Returns:
        Statistics including question counts, difficulty distribution, Bloom's levels
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"
    
    stats = db.get_bank_statistics(bank_id)
    
    # Format average difficulty
    avg_diff = stats['avg_difficulty']
    avg_diff_str = f"{avg_diff:.2f}" if avg_diff is not None else "N/A"
    
    result = f"""
## 📊 Statistics for "{bank['name']}"

### Overview
- **Total Questions:** {stats['total_questions']}
- **Active:** {stats['active_questions']} | **Drafts:** {stats['draft_questions']}
- **Average Difficulty:** {avg_diff_str} (0=easy, 1=hard)
- **Total Points:** {stats['total_points'] or 0}

### By Question Type
"""
    for qtype, count in stats['by_type'].items():
        result += f"- {qtype.replace('_', ' ').title()}: {count}\n"
    
    result += "\n### By Difficulty\n"
    result += f"- Easy (< 0.3): {stats['by_difficulty']['easy']}\n"
    result += f"- Medium (0.3-0.7): {stats['by_difficulty']['medium']}\n"
    result += f"- Hard (> 0.7): {stats['by_difficulty']['hard']}\n"
    
    if stats['by_bloom_level']:
        result += "\n### By Bloom's Taxonomy\n"
        bloom_order = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
        for level in bloom_order:
            if level in stats['by_bloom_level']:
                result += f"- {level.title()}: {stats['by_bloom_level'][level]}\n"
    
    if stats['by_topic']:
        result += "\n### By Topic\n"
        for topic, count in stats['by_topic'].items():
            result += f"- {topic}: {count}\n"
    
    return result


@mcp.tool()
def delete_question_bank(bank_id: str) -> str:
    """
    Delete a question bank and all its questions and topics.

    This is a destructive operation — all questions, topics, and tags in the bank
    will be permanently deleted.

    Args:
        bank_id: The question bank ID to delete

    Returns:
        Confirmation message
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"

    stats = db.get_bank_statistics(bank_id)
    success = db.delete_question_bank(bank_id)

    if success:
        return (
            f"✅ Question bank deleted: **{bank['name']}**\n\n"
            f"Removed {stats['total_questions']} question(s) and "
            f"all associated topics and tags."
        )
    else:
        return "Failed to delete question bank."


# ============================================================
# TOPIC TOOLS
# ============================================================

@mcp.tool()
def create_topic(
    bank_id: str,
    name: str,
    description: str = None,
    parent_topic_id: str = None
) -> str:
    """
    Create a topic within a question bank for organizing questions.
    
    Args:
        bank_id: The question bank ID
        name: Topic name (e.g., "Linear Equations", "Photosynthesis")
        description: Optional description of what this topic covers
        parent_topic_id: Optional parent topic ID for hierarchical organization
    
    Returns:
        Confirmation with topic details
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"
    
    topic_id = f"topic-{uuid.uuid4().hex[:8]}"
    
    topic = db.create_topic(
        topic_id=topic_id,
        bank_id=bank_id,
        name=name,
        parent_id=parent_topic_id,
        description=description
    )
    
    return f"""
✅ Topic Created!

**ID:** `{topic['id']}`
**Name:** {topic['name']}
**Bank:** {bank['name']}
**Parent:** {topic['parent_id'] or 'None (top-level)'}

Use this topic ID when creating questions.
"""


@mcp.tool()
def list_topics(bank_id: str) -> str:
    """
    List all topics in a question bank.
    
    Args:
        bank_id: The question bank ID
    
    Returns:
        List of topics with question counts
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"
    
    topics = db.list_topics(bank_id)
    
    if not topics:
        return f"No topics in '{bank['name']}'. Create one with `create_topic`."
    
    result = f"**Topics in '{bank['name']}':**\n\n"
    
    for topic in topics:
        indent = "  " if topic['parent_id'] else ""
        result += f"{indent}- **{topic['name']}** (`{topic['id']}`)\n"
        result += f"{indent}  Questions: {topic['question_count']}\n"
        if topic['description']:
            result += f"{indent}  {topic['description']}\n"
    
    return result


@mcp.tool()
def delete_topic(bank_id: str, topic_id: str) -> str:
    """
    Delete a topic from a question bank.

    Questions linked to this topic will be unlinked but not deleted.

    Args:
        bank_id: The question bank ID
        topic_id: The topic ID to delete

    Returns:
        Confirmation message
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"

    topics = db.list_topics(bank_id)
    topic = next((t for t in topics if t['id'] == topic_id), None)
    if not topic:
        return f"Topic not found in this bank: {topic_id}"

    success = db.delete_topic(topic_id)

    if success:
        return (
            f"✅ Topic deleted: **{topic['name']}**\n\n"
            f"{topic['question_count']} question(s) were unlinked from this topic "
            f"but remain in the bank."
        )
    else:
        return "Failed to delete topic."


# ============================================================
# QUESTION TOOLS
# ============================================================

@mcp.tool()
def create_question(
    bank_id: str,
    question_type: str,
    stem: str,
    correct_answer: str,
    options: list = None,
    explanation: str = None,
    difficulty: float = 0.5,
    bloom_level: str = None,
    estimated_time_seconds: int = 60,
    points: int = 1,
    topic_ids: list = None,
    tags: list = None
) -> str:
    """
    Create a new question in a question bank.
    
    Args:
        bank_id: The question bank ID
        question_type: Type of question - "multiple_choice", "true_false", "short_answer", "essay"
        stem: The question text
        correct_answer: The correct answer (or rubric for essays)
        options: List of answer choices for multiple choice (e.g., ["A", "B", "C", "D"])
        explanation: Explanation of why the answer is correct
        difficulty: Difficulty from 0.0 (easy) to 1.0 (hard), default 0.5
        bloom_level: Bloom's taxonomy level - "remember", "understand", "apply", "analyze", "evaluate", "create"
        estimated_time_seconds: Expected time to answer in seconds, default 60
        points: Point value, default 1
        topic_ids: List of topic IDs this question belongs to
        tags: List of tags for flexible categorization
    
    Returns:
        The created question with all details
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"
    
    valid_types = ['multiple_choice', 'true_false', 'short_answer', 'essay']
    if question_type not in valid_types:
        return f"Invalid question type. Must be one of: {', '.join(valid_types)}"
    
    valid_bloom = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
    if bloom_level and bloom_level not in valid_bloom:
        return f"Invalid Bloom's level. Must be one of: {', '.join(valid_bloom)}"
    
    if question_type == 'multiple_choice' and not options:
        return "Multiple choice questions require options."

    if not (0.0 <= difficulty <= 1.0):
        return "Difficulty must be between 0.0 and 1.0."

    if points < 0:
        return "Points must be non-negative."

    if estimated_time_seconds < 1:
        return "Estimated time must be at least 1 second."

    question_id = f"q-{uuid.uuid4().hex[:8]}"
    
    question = db.create_question(
        question_id=question_id,
        bank_id=bank_id,
        question_type=question_type,
        stem=stem,
        correct_answer=correct_answer,
        options=options,
        explanation=explanation,
        difficulty=difficulty,
        bloom_level=bloom_level,
        estimated_time_seconds=estimated_time_seconds,
        points=points,
        topics=topic_ids,
        tags=tags,
        status="draft"
    )
    
    return _format_question(question, show_answer=True)


@mcp.tool()
def get_question(question_id: str, show_answer: bool = True) -> str:
    """
    Get a question by ID.
    
    Args:
        question_id: The question ID
        show_answer: Whether to show the correct answer (default True)
    
    Returns:
        Question details
    """
    question = db.get_question(question_id)
    
    if not question:
        return f"Question not found: {question_id}"
    
    return _format_question(question, show_answer=show_answer)


@mcp.tool()
def update_question(
    question_id: str,
    stem: str = None,
    correct_answer: str = None,
    options: list = None,
    explanation: str = None,
    difficulty: float = None,
    bloom_level: str = None,
    estimated_time_seconds: int = None,
    points: int = None,
    topic_ids: list = None,
    tags: list = None,
    status: str = None
) -> str:
    """
    Update an existing question.
    
    Args:
        question_id: The question ID to update
        stem: New question text
        correct_answer: New correct answer
        options: New answer options (for multiple choice)
        explanation: New explanation
        difficulty: New difficulty (0.0-1.0)
        bloom_level: New Bloom's level
        estimated_time_seconds: New time estimate
        points: New point value
        topic_ids: New list of topic IDs (replaces existing)
        tags: New list of tags (replaces existing)
        status: New status - "draft", "active", "archived"
    
    Returns:
        Updated question details
    """
    existing = db.get_question(question_id)
    if not existing:
        return f"Question not found: {question_id}"

    valid_bloom = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
    if bloom_level is not None and bloom_level not in valid_bloom:
        return f"Invalid Bloom's level. Must be one of: {', '.join(valid_bloom)}"

    valid_status = ['draft', 'active', 'archived']
    if status is not None and status not in valid_status:
        return f"Invalid status. Must be one of: {', '.join(valid_status)}"

    if difficulty is not None and not (0.0 <= difficulty <= 1.0):
        return "Difficulty must be between 0.0 and 1.0."

    if points is not None and points < 0:
        return "Points must be non-negative."

    if estimated_time_seconds is not None and estimated_time_seconds < 1:
        return "Estimated time must be at least 1 second."

    updates = {}
    if stem is not None: updates['stem'] = stem
    if correct_answer is not None: updates['correct_answer'] = correct_answer
    if options is not None: updates['options'] = options
    if explanation is not None: updates['explanation'] = explanation
    if difficulty is not None: updates['difficulty'] = difficulty
    if bloom_level is not None: updates['bloom_level'] = bloom_level
    if estimated_time_seconds is not None: updates['estimated_time_seconds'] = estimated_time_seconds
    if points is not None: updates['points'] = points
    if topic_ids is not None: updates['topics'] = topic_ids
    if tags is not None: updates['tags'] = tags
    if status is not None: updates['status'] = status
    
    if not updates:
        return "No updates provided."
    
    question = db.update_question(question_id, **updates)
    
    return f"✅ Question updated!\n\n{_format_question(question, show_answer=True)}"


@mcp.tool()
def delete_question(question_id: str) -> str:
    """
    Delete a question.
    
    Args:
        question_id: The question ID to delete
    
    Returns:
        Confirmation message
    """
    question = db.get_question(question_id)
    if not question:
        return f"Question not found: {question_id}"
    
    success = db.delete_question(question_id)
    
    if success:
        return f"✅ Question deleted: {question_id}\n\nDeleted: {question['stem'][:50]}..."
    else:
        return "Failed to delete question."


@mcp.tool()
def search_questions(
    bank_id: str = None,
    topic_id: str = None,
    question_type: str = None,
    bloom_level: str = None,
    difficulty_min: float = None,
    difficulty_max: float = None,
    status: str = None,
    tags: list = None,
    search_text: str = None,
    limit: int = 20
) -> str:
    """
    Search questions with filters.
    
    Args:
        bank_id: Filter by question bank
        topic_id: Filter by topic
        question_type: Filter by type - "multiple_choice", "true_false", "short_answer", "essay"
        bloom_level: Filter by Bloom's level
        difficulty_min: Minimum difficulty (0.0-1.0)
        difficulty_max: Maximum difficulty (0.0-1.0)
        status: Filter by status - "draft", "active", "archived"
        tags: Filter by tags (questions must have at least one)
        search_text: Search in question stem and explanation
        limit: Maximum results to return (default 20)
    
    Returns:
        List of matching questions
    """
    limit = max(1, min(limit, 100))

    questions = db.search_questions(
        bank_id=bank_id,
        topic_id=topic_id,
        question_type=question_type,
        bloom_level=bloom_level,
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        status=status,
        tags=tags,
        search_text=search_text,
        limit=limit
    )
    
    if not questions:
        return "No questions found matching your criteria."
    
    result = f"**Found {len(questions)} question(s):**\n\n"
    
    for q in questions:
        difficulty_label = "Easy" if q['difficulty'] < 0.3 else "Medium" if q['difficulty'] < 0.7 else "Hard"
        result += f"### `{q['id']}` - {q['question_type'].replace('_', ' ').title()}\n"
        result += f"{q['stem'][:100]}{'...' if len(q['stem']) > 100 else ''}\n"
        result += f"- Difficulty: {difficulty_label} ({q['difficulty']:.1f}) | "
        result += f"Bloom: {q['bloom_level'] or 'N/A'} | "
        result += f"Status: {q['status']} | Points: {q['points']}\n\n"
    
    return result


@mcp.tool()
def activate_questions(question_ids: list) -> str:
    """
    Activate multiple questions (change status from draft to active).
    
    Args:
        question_ids: List of question IDs to activate
    
    Returns:
        Confirmation of activated questions
    """
    activated = []
    errors = []
    
    for qid in question_ids:
        question = db.get_question(qid)
        if not question:
            errors.append(f"{qid}: not found")
        elif question['status'] == 'active':
            errors.append(f"{qid}: already active")
        else:
            db.update_question(qid, status='active')
            activated.append(qid)
    
    result = f"✅ Activated {len(activated)} question(s)\n"
    
    if activated:
        result += "\nActivated:\n"
        for qid in activated:
            result += f"- `{qid}`\n"
    
    if errors:
        result += "\nSkipped:\n"
        for err in errors:
            result += f"- {err}\n"
    
    return result


@mcp.tool()
def suggest_questions(
    bank_id: str,
    topic: str,
    count: int = 5,
    difficulty: str = "mixed",
    bloom_levels: list = None
) -> str:
    """
    Get suggestions for questions to create based on topic and requirements.
    
    This tool helps teachers brainstorm question ideas.
    
    Args:
        bank_id: The question bank ID
        topic: Topic or learning objective to create questions for
        count: Number of question suggestions (default 5)
        difficulty: "easy", "medium", "hard", or "mixed" (default)
        bloom_levels: List of Bloom's levels to include, or None for all
    
    Returns:
        Suggestions for questions to create (not actual questions - teacher should review and create)
    """
    bank = db.get_question_bank(bank_id)
    if not bank:
        return f"Question bank not found: {bank_id}"
    
    bloom_descriptions = {
        'remember': 'recall facts, terms, concepts',
        'understand': 'explain ideas, interpret meaning',
        'apply': 'use knowledge in new situations',
        'analyze': 'break down, compare, contrast',
        'evaluate': 'justify, critique, make judgments',
        'create': 'design, construct, produce new work'
    }
    
    if bloom_levels is None:
        bloom_levels = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
    
    result = f"""
## 💡 Question Suggestions for "{topic}"

**Bank:** {bank['name']}
**Subject:** {bank['subject']}
**Difficulty:** {difficulty}

Here are {count} question ideas across different Bloom's levels:

"""
    
    suggestion_num = 1
    for bloom in bloom_levels:
        if suggestion_num > count:
            break
            
        diff_value = 0.3 if difficulty == 'easy' else 0.7 if difficulty == 'hard' else 0.5
        
        result += f"""
### Suggestion {suggestion_num}: {bloom.title()} Level
- **Bloom's Level:** {bloom} ({bloom_descriptions[bloom]})
- **Suggested Difficulty:** {diff_value}
- **Question Type:** {"multiple_choice" if bloom in ['remember', 'understand'] else "short_answer" if bloom in ['apply', 'analyze'] else "essay"}

**Prompt idea:** Create a question that asks students to {bloom_descriptions[bloom]} related to {topic}.

To create this question, use `create_question` with:
- `bloom_level`: "{bloom}"
- `difficulty`: {diff_value}

---
"""
        suggestion_num += 1
    
    result += """
**Next steps:**
1. Review these suggestions
2. Write the actual question stems
3. Use `create_question` to add them to the bank
4. Use `activate_questions` when ready to use them
"""
    
    return result


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _format_question(question: dict, show_answer: bool = True) -> str:
    """Format a question for display."""
    difficulty_label = "Easy" if question['difficulty'] < 0.3 else "Medium" if question['difficulty'] < 0.7 else "Hard"
    
    result = f"""
## Question: `{question['id']}`

**Type:** {question['question_type'].replace('_', ' ').title()}
**Status:** {question['status'].title()}
**Difficulty:** {difficulty_label} ({question['difficulty']:.2f})
**Bloom's Level:** {question['bloom_level'] or 'Not set'}
**Points:** {question['points']} | **Est. Time:** {question['estimated_time_seconds']}s

### Stem
{question['stem']}
"""
    
    if question['options']:
        result += "\n### Options\n"
        for i, opt in enumerate(question['options']):
            letter = chr(65 + i)  # A, B, C, D...
            result += f"- **{letter}.** {opt}\n"
    
    if show_answer:
        result += f"\n### Correct Answer\n{question['correct_answer']}\n"
        
        if question['explanation']:
            result += f"\n### Explanation\n{question['explanation']}\n"
    
    if question['topics']:
        topics_str = ", ".join(t['name'] for t in question['topics'])
        result += f"\n**Topics:** {topics_str}\n"
    
    if question['tags']:
        result += f"**Tags:** {', '.join(question['tags'])}\n"
    
    return result


# ============================================================
# RESOURCES
# ============================================================

@mcp.resource("questionbank://blooms-taxonomy")
def blooms_taxonomy_resource() -> str:
    """Bloom's Taxonomy reference for question classification."""
    return """
# Bloom's Taxonomy for Question Classification

## Levels (Lower to Higher Order Thinking)

### 1. Remember
- **Definition:** Recall facts and basic concepts
- **Verbs:** define, list, name, identify, recall, recognize
- **Example:** "What is the formula for the area of a circle?"

### 2. Understand
- **Definition:** Explain ideas or concepts
- **Verbs:** describe, explain, summarize, interpret, classify
- **Example:** "Explain why plants need sunlight for photosynthesis."

### 3. Apply
- **Definition:** Use information in new situations
- **Verbs:** solve, use, demonstrate, calculate, apply
- **Example:** "Calculate the area of a circle with radius 5cm."

### 4. Analyze
- **Definition:** Draw connections among ideas
- **Verbs:** compare, contrast, analyze, differentiate, examine
- **Example:** "Compare and contrast mitosis and meiosis."

### 5. Evaluate
- **Definition:** Justify a decision or course of action
- **Verbs:** evaluate, judge, critique, defend, assess
- **Example:** "Evaluate the effectiveness of the New Deal policies."

### 6. Create
- **Definition:** Produce new or original work
- **Verbs:** design, construct, develop, formulate, create
- **Example:** "Design an experiment to test the effect of pH on enzyme activity."

## Tips for Question Writing

- **Mix levels** in assessments for comprehensive evaluation
- **Higher levels** (analyze, evaluate, create) are harder to guess
- **Lower levels** are good for checking foundational knowledge
- **Match level to learning objectives**
"""


@mcp.resource("questionbank://question-types")
def question_types_resource() -> str:
    """Question type reference."""
    return """
# Question Types

## Multiple Choice
- Best for: Knowledge recall, concept recognition
- Difficulty range: Easy to Medium
- Grading: Automatic
- Tip: Use plausible distractors

## True/False
- Best for: Quick fact checking
- Difficulty range: Easy
- Grading: Automatic
- Tip: Avoid "always" and "never"

## Short Answer
- Best for: Recall, simple application
- Difficulty range: Easy to Medium
- Grading: Semi-automatic (keyword matching)
- Tip: Be specific about expected length

## Essay
- Best for: Analysis, evaluation, creation
- Difficulty range: Medium to Hard
- Grading: Manual with rubric
- Tip: Provide clear criteria
"""


# ============================================================
# MAIN
# ============================================================

def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
