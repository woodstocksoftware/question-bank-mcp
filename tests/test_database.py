"""Tests for the database layer (src/question_bank/database.py)."""

import json
import pytest

from src.question_bank import database as db


# ── helpers ──────────────────────────────────────────────────

def _make_bank(bank_id="bank-0001", name="Algebra I", subject="Math", **kw):
    return db.create_question_bank(bank_id, name, subject, **kw)


def _make_topic(topic_id="topic-0001", bank_id="bank-0001", name="Linear Eqs", **kw):
    return db.create_topic(topic_id, bank_id, name, **kw)


def _make_question(question_id="q-0001", bank_id="bank-0001", **kw):
    defaults = dict(
        question_type="multiple_choice",
        stem="What is 2+2?",
        correct_answer="4",
        options=["3", "4", "5", "6"],
        difficulty=0.3,
        bloom_level="remember",
    )
    defaults.update(kw)
    return db.create_question(question_id, bank_id, **defaults)


# ── question bank CRUD ───────────────────────────────────────

class TestQuestionBanks:
    def test_create_bank(self):
        bank = _make_bank()
        assert bank["id"] == "bank-0001"
        assert bank["name"] == "Algebra I"
        assert bank["subject"] == "Math"

    def test_create_bank_with_optional_fields(self):
        bank = _make_bank(description="Intro algebra", grade_level="9th")
        assert bank["description"] == "Intro algebra"
        assert bank["grade_level"] == "9th"

    def test_list_banks_empty(self):
        assert db.list_question_banks() == []

    def test_list_banks(self):
        _make_bank("bank-a", "A", "Math")
        _make_bank("bank-b", "B", "Science")
        banks = db.list_question_banks()
        assert len(banks) == 2
        assert all("question_count" in b for b in banks)

    def test_get_bank(self):
        _make_bank()
        bank = db.get_question_bank("bank-0001")
        assert bank is not None
        assert bank["name"] == "Algebra I"

    def test_get_bank_not_found(self):
        assert db.get_question_bank("bank-nope") is None

    def test_delete_bank(self):
        _make_bank()
        assert db.delete_question_bank("bank-0001") is True
        assert db.get_question_bank("bank-0001") is None

    def test_delete_bank_not_found(self):
        assert db.delete_question_bank("bank-nope") is False

    def test_delete_bank_cascades(self):
        _make_bank()
        _make_topic()
        _make_question()
        db.delete_question_bank("bank-0001")
        assert db.get_question("q-0001") is None
        assert db.list_topics("bank-0001") == []

    def test_get_bank_statistics_empty(self):
        _make_bank()
        stats = db.get_bank_statistics("bank-0001")
        assert stats["total_questions"] == 0
        assert stats["by_type"] == {}

    def test_get_bank_statistics_populated(self):
        _make_bank()
        _make_topic()
        _make_question(difficulty=0.2, topics=["topic-0001"], tags=["algebra"])
        stats = db.get_bank_statistics("bank-0001")
        assert stats["total_questions"] == 1
        assert stats["by_type"]["multiple_choice"] == 1
        assert stats["by_bloom_level"]["remember"] == 1
        assert stats["by_difficulty"]["easy"] == 1
        assert stats["by_topic"]["Linear Eqs"] == 1


# ── topics ───────────────────────────────────────────────────

class TestTopics:
    def test_create_topic(self):
        _make_bank()
        topic = _make_topic()
        assert topic["id"] == "topic-0001"
        assert topic["bank_id"] == "bank-0001"

    def test_list_topics(self):
        _make_bank()
        _make_topic("topic-a", name="A")
        _make_topic("topic-b", name="B")
        topics = db.list_topics("bank-0001")
        assert len(topics) == 2

    def test_delete_topic_unlinks_questions(self):
        _make_bank()
        _make_topic()
        _make_question(topics=["topic-0001"])
        db.delete_topic("topic-0001")
        q = db.get_question("q-0001")
        assert q is not None  # question still exists
        assert q["topics"] == []  # but unlinked

    def test_hierarchical_topics(self):
        _make_bank()
        _make_topic("topic-parent", name="Algebra")
        _make_topic("topic-child", name="Quadratics", parent_id="topic-parent")
        topics = db.list_topics("bank-0001")
        child = next(t for t in topics if t["id"] == "topic-child")
        assert child["parent_id"] == "topic-parent"

    def test_delete_topic_not_found(self):
        assert db.delete_topic("topic-nope") is False


# ── questions ────────────────────────────────────────────────

class TestQuestions:
    def test_create_question(self):
        _make_bank()
        q = _make_question()
        assert q["id"] == "q-0001"
        assert q["question_type"] == "multiple_choice"
        assert q["options"] == ["3", "4", "5", "6"]

    def test_get_question(self):
        _make_bank()
        _make_question()
        q = db.get_question("q-0001")
        assert q is not None
        assert q["stem"] == "What is 2+2?"

    def test_get_question_not_found(self):
        assert db.get_question("q-nope") is None

    def test_create_question_with_topics_and_tags(self):
        _make_bank()
        _make_topic()
        q = _make_question(topics=["topic-0001"], tags=["Algebra", "Basic"])
        assert len(q["topics"]) == 1
        assert q["topics"][0]["id"] == "topic-0001"
        assert set(q["tags"]) == {"algebra", "basic"}  # lowercased

    def test_update_question_fields(self):
        _make_bank()
        _make_question()
        updated = db.update_question("q-0001", stem="New stem", difficulty=0.9)
        assert updated["stem"] == "New stem"
        assert updated["difficulty"] == 0.9

    def test_update_question_replaces_topics(self):
        _make_bank()
        _make_topic("topic-a", name="A")
        _make_topic("topic-b", name="B")
        _make_question(topics=["topic-a"])
        updated = db.update_question("q-0001", topics=["topic-b"])
        assert [t["id"] for t in updated["topics"]] == ["topic-b"]

    def test_update_question_replaces_tags(self):
        _make_bank()
        _make_question(tags=["old"])
        updated = db.update_question("q-0001", tags=["New"])
        assert updated["tags"] == ["new"]  # lowercased

    def test_update_question_invalid_column(self):
        _make_bank()
        _make_question()
        with pytest.raises(ValueError, match="Invalid column"):
            db.update_question("q-0001", evil_column="drop table")

    def test_delete_question(self):
        _make_bank()
        _make_question()
        assert db.delete_question("q-0001") is True
        assert db.get_question("q-0001") is None

    def test_delete_question_not_found(self):
        assert db.delete_question("q-nope") is False

    def test_json_options_round_trip(self):
        _make_bank()
        opts = ["α", "β", "γ", "δ"]
        _make_question(options=opts)
        q = db.get_question("q-0001")
        assert q["options"] == opts

    def test_question_without_options(self):
        _make_bank()
        _make_question(question_type="short_answer", options=None)
        q = db.get_question("q-0001")
        assert q["options"] is None

    def test_update_options_json(self):
        _make_bank()
        _make_question()
        new_opts = ["A", "B"]
        updated = db.update_question("q-0001", options=new_opts)
        assert updated["options"] == new_opts


# ── search ───────────────────────────────────────────────────

class TestSearch:
    @pytest.fixture(autouse=True)
    def _seed(self):
        _make_bank()
        _make_topic()
        _make_question("q-mc", difficulty=0.2, bloom_level="remember",
                       topics=["topic-0001"], tags=["algebra"],
                       stem="MC question about algebra")
        _make_question("q-tf", question_type="true_false",
                       difficulty=0.8, bloom_level="analyze",
                       stem="TF question about analysis",
                       options=None, tags=["logic"])

    def test_search_by_bank(self):
        results = db.search_questions(bank_id="bank-0001")
        assert len(results) == 2

    def test_search_by_topic(self):
        results = db.search_questions(topic_id="topic-0001")
        assert len(results) == 1
        assert results[0]["id"] == "q-mc"

    def test_search_by_type(self):
        results = db.search_questions(question_type="true_false")
        assert len(results) == 1

    def test_search_by_bloom(self):
        results = db.search_questions(bloom_level="analyze")
        assert len(results) == 1

    def test_search_by_difficulty_range(self):
        results = db.search_questions(difficulty_min=0.5, difficulty_max=1.0)
        assert len(results) == 1
        assert results[0]["id"] == "q-tf"

    def test_search_by_tags(self):
        results = db.search_questions(tags=["algebra"])
        assert len(results) == 1

    def test_search_by_text(self):
        results = db.search_questions(search_text="analysis")
        assert len(results) == 1
        assert results[0]["id"] == "q-tf"

    def test_search_limit(self):
        results = db.search_questions(bank_id="bank-0001", limit=1)
        assert len(results) == 1

    def test_search_no_results(self):
        results = db.search_questions(question_type="essay")
        assert results == []

    def test_search_by_status(self):
        results = db.search_questions(status="active")
        assert results == []  # all are draft
