"""
Question Bank database with schema for educational assessments.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "question_bank.db"


def get_connection():
    """Get database connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize database with schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        -- Question Banks (collections of questions for a course/test)
        CREATE TABLE IF NOT EXISTS question_banks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT NOT NULL,
            grade_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Topics (hierarchical topic taxonomy)
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            name TEXT NOT NULL,
            parent_id TEXT,
            description TEXT,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES topics(id) ON DELETE SET NULL
        );
        
        -- Questions
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            
            -- Content
            question_type TEXT NOT NULL,  -- multiple_choice, true_false, short_answer, essay
            stem TEXT NOT NULL,           -- The question text
            options TEXT,                 -- JSON array for multiple choice
            correct_answer TEXT,          -- Answer or JSON for multiple correct
            explanation TEXT,             -- Why the answer is correct
            
            -- Difficulty & Classification
            difficulty REAL DEFAULT 0.5,  -- 0.0 (easy) to 1.0 (hard)
            bloom_level TEXT,             -- remember, understand, apply, analyze, evaluate, create
            estimated_time_seconds INTEGER DEFAULT 60,
            points INTEGER DEFAULT 1,
            
            -- Metadata
            status TEXT DEFAULT 'draft',  -- draft, active, archived
            author TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            -- Usage statistics (updated after tests)
            times_used INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            avg_time_seconds REAL,
            discrimination_index REAL,    -- How well it separates high/low performers
            
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
        );
        
        -- Question-Topic mapping (many-to-many)
        CREATE TABLE IF NOT EXISTS question_topics (
            question_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            PRIMARY KEY (question_id, topic_id),
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );
        
        -- Tags for flexible categorization
        CREATE TABLE IF NOT EXISTS question_tags (
            question_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (question_id, tag),
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_questions_bank ON questions(bank_id);
        CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
        CREATE INDEX IF NOT EXISTS idx_questions_bloom ON questions(bloom_level);
        CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);
        CREATE INDEX IF NOT EXISTS idx_topics_bank ON topics(bank_id);
    """)
    
    conn.commit()
    conn.close()


# Initialize on import
init_database()


# ============================================================
# QUESTION BANK OPERATIONS
# ============================================================

def create_question_bank(bank_id: str, name: str, subject: str, 
                         description: str = None, grade_level: str = None) -> dict:
    """Create a new question bank."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO question_banks (id, name, description, subject, grade_level)
        VALUES (?, ?, ?, ?, ?)
    """, (bank_id, name, description, subject, grade_level))
    
    conn.commit()
    conn.close()
    
    return {
        "id": bank_id,
        "name": name,
        "subject": subject,
        "description": description,
        "grade_level": grade_level
    }


def list_question_banks() -> list:
    """List all question banks."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT qb.*, 
               COUNT(DISTINCT q.id) as question_count,
               COUNT(DISTINCT t.id) as topic_count
        FROM question_banks qb
        LEFT JOIN questions q ON q.bank_id = qb.id
        LEFT JOIN topics t ON t.bank_id = qb.id
        GROUP BY qb.id
        ORDER BY qb.updated_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_question_bank(bank_id: str) -> Optional[dict]:
    """Get a question bank by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM question_banks WHERE id = ?", (bank_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_bank_statistics(bank_id: str) -> dict:
    """Get detailed statistics for a question bank."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Basic counts
    cursor.execute("""
        SELECT 
            COUNT(*) as total_questions,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_questions,
            COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_questions,
            AVG(difficulty) as avg_difficulty,
            SUM(points) as total_points
        FROM questions WHERE bank_id = ?
    """, (bank_id,))
    basic = dict(cursor.fetchone())
    
    # By question type
    cursor.execute("""
        SELECT question_type, COUNT(*) as count
        FROM questions WHERE bank_id = ?
        GROUP BY question_type
    """, (bank_id,))
    by_type = {row['question_type']: row['count'] for row in cursor.fetchall()}
    
    # By Bloom's level
    cursor.execute("""
        SELECT bloom_level, COUNT(*) as count
        FROM questions WHERE bank_id = ? AND bloom_level IS NOT NULL
        GROUP BY bloom_level
    """, (bank_id,))
    by_bloom = {row['bloom_level']: row['count'] for row in cursor.fetchall()}
    
    # By difficulty range
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN difficulty < 0.3 THEN 1 END) as easy,
            COUNT(CASE WHEN difficulty >= 0.3 AND difficulty < 0.7 THEN 1 END) as medium,
            COUNT(CASE WHEN difficulty >= 0.7 THEN 1 END) as hard
        FROM questions WHERE bank_id = ?
    """, (bank_id,))
    by_difficulty = dict(cursor.fetchone())
    
    # Topics
    cursor.execute("""
        SELECT t.name, COUNT(qt.question_id) as question_count
        FROM topics t
        LEFT JOIN question_topics qt ON qt.topic_id = t.id
        WHERE t.bank_id = ?
        GROUP BY t.id
        ORDER BY question_count DESC
    """, (bank_id,))
    by_topic = {row['name']: row['question_count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        **basic,
        "by_type": by_type,
        "by_bloom_level": by_bloom,
        "by_difficulty": by_difficulty,
        "by_topic": by_topic
    }


# ============================================================
# TOPIC OPERATIONS
# ============================================================

def create_topic(topic_id: str, bank_id: str, name: str, 
                 parent_id: str = None, description: str = None) -> dict:
    """Create a topic within a question bank."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO topics (id, bank_id, name, parent_id, description)
        VALUES (?, ?, ?, ?, ?)
    """, (topic_id, bank_id, name, parent_id, description))
    
    conn.commit()
    conn.close()
    
    return {"id": topic_id, "bank_id": bank_id, "name": name, 
            "parent_id": parent_id, "description": description}


def list_topics(bank_id: str) -> list:
    """List all topics for a question bank."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, COUNT(qt.question_id) as question_count
        FROM topics t
        LEFT JOIN question_topics qt ON qt.topic_id = t.id
        WHERE t.bank_id = ?
        GROUP BY t.id
        ORDER BY t.name
    """, (bank_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================
# QUESTION OPERATIONS
# ============================================================

def create_question(
    question_id: str,
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
    topics: list = None,
    tags: list = None,
    author: str = None,
    status: str = "draft"
) -> dict:
    """Create a new question."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO questions 
        (id, bank_id, question_type, stem, options, correct_answer, explanation,
         difficulty, bloom_level, estimated_time_seconds, points, author, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        question_id, bank_id, question_type, stem,
        json.dumps(options) if options else None,
        correct_answer, explanation, difficulty, bloom_level,
        estimated_time_seconds, points, author, status
    ))
    
    # Add topics
    if topics:
        for topic_id in topics:
            cursor.execute("""
                INSERT OR IGNORE INTO question_topics (question_id, topic_id)
                VALUES (?, ?)
            """, (question_id, topic_id))
    
    # Add tags
    if tags:
        for tag in tags:
            cursor.execute("""
                INSERT OR IGNORE INTO question_tags (question_id, tag)
                VALUES (?, ?)
            """, (question_id, tag.lower()))
    
    conn.commit()
    conn.close()
    
    return get_question(question_id)


def get_question(question_id: str) -> Optional[dict]:
    """Get a question by ID with all related data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    question = dict(row)
    question['options'] = json.loads(question['options']) if question['options'] else None
    
    # Get topics
    cursor.execute("""
        SELECT t.id, t.name FROM topics t
        JOIN question_topics qt ON qt.topic_id = t.id
        WHERE qt.question_id = ?
    """, (question_id,))
    question['topics'] = [{"id": r['id'], "name": r['name']} for r in cursor.fetchall()]
    
    # Get tags
    cursor.execute("SELECT tag FROM question_tags WHERE question_id = ?", (question_id,))
    question['tags'] = [r['tag'] for r in cursor.fetchall()]
    
    conn.close()
    return question


def update_question(question_id: str, **updates) -> Optional[dict]:
    """Update a question."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Handle special fields
    topics = updates.pop('topics', None)
    tags = updates.pop('tags', None)
    
    if 'options' in updates and updates['options'] is not None:
        updates['options'] = json.dumps(updates['options'])
    
    # Build update query
    if updates:
        updates['updated_at'] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        cursor.execute(
            f"UPDATE questions SET {set_clause} WHERE id = ?",
            list(updates.values()) + [question_id]
        )
    
    # Update topics if provided
    if topics is not None:
        cursor.execute("DELETE FROM question_topics WHERE question_id = ?", (question_id,))
        for topic_id in topics:
            cursor.execute("""
                INSERT INTO question_topics (question_id, topic_id) VALUES (?, ?)
            """, (question_id, topic_id))
    
    # Update tags if provided
    if tags is not None:
        cursor.execute("DELETE FROM question_tags WHERE question_id = ?", (question_id,))
        for tag in tags:
            cursor.execute("""
                INSERT INTO question_tags (question_id, tag) VALUES (?, ?)
            """, (question_id, tag.lower()))
    
    conn.commit()
    conn.close()
    
    return get_question(question_id)


def delete_question(question_id: str) -> bool:
    """Delete a question."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected > 0


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
    limit: int = 50,
    offset: int = 0
) -> list:
    """Search questions with filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT DISTINCT q.* FROM questions q"
    joins = []
    conditions = []
    params = []
    
    if topic_id:
        joins.append("JOIN question_topics qt ON qt.question_id = q.id")
        conditions.append("qt.topic_id = ?")
        params.append(topic_id)
    
    if tags:
        joins.append("JOIN question_tags tg ON tg.question_id = q.id")
        placeholders = ",".join("?" * len(tags))
        conditions.append(f"tg.tag IN ({placeholders})")
        params.extend([t.lower() for t in tags])
    
    if bank_id:
        conditions.append("q.bank_id = ?")
        params.append(bank_id)
    
    if question_type:
        conditions.append("q.question_type = ?")
        params.append(question_type)
    
    if bloom_level:
        conditions.append("q.bloom_level = ?")
        params.append(bloom_level)
    
    if difficulty_min is not None:
        conditions.append("q.difficulty >= ?")
        params.append(difficulty_min)
    
    if difficulty_max is not None:
        conditions.append("q.difficulty <= ?")
        params.append(difficulty_max)
    
    if status:
        conditions.append("q.status = ?")
        params.append(status)
    
    if search_text:
        conditions.append("(q.stem LIKE ? OR q.explanation LIKE ?)")
        params.extend([f"%{search_text}%", f"%{search_text}%"])
    
    # Build final query
    if joins:
        query += " " + " ".join(joins)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY q.updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        q = dict(row)
        q['options'] = json.loads(q['options']) if q['options'] else None
        questions.append(q)
    
    return questions


if __name__ == "__main__":
    # Test the database
    print("Testing Question Bank Database...")
    
    # Create a test bank
    bank = create_question_bank(
        "math-101", 
        "Algebra I", 
        "Mathematics",
        "Introduction to Algebra",
        "9th Grade"
    )
    print(f"\nCreated bank: {bank['name']}")
    
    # Create topics
    create_topic("alg-linear", "math-101", "Linear Equations")
    create_topic("alg-quad", "math-101", "Quadratic Equations")
    print("Created topics")
    
    # Create a question
    q = create_question(
        question_id="q-001",
        bank_id="math-101",
        question_type="multiple_choice",
        stem="What is the solution to 2x + 4 = 10?",
        options=["x = 2", "x = 3", "x = 4", "x = 5"],
        correct_answer="x = 3",
        explanation="Subtract 4 from both sides: 2x = 6. Divide by 2: x = 3.",
        difficulty=0.3,
        bloom_level="apply",
        topics=["alg-linear"],
        tags=["solving", "basic"]
    )
    print(f"\nCreated question: {q['stem'][:50]}...")
    
    # Get statistics
    stats = get_bank_statistics("math-101")
    print(f"\nBank statistics:")
    print(f"  Total questions: {stats['total_questions']}")
    print(f"  Avg difficulty: {stats['avg_difficulty']}")
    
    print("\n✅ Database test complete!")
