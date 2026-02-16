"""Tests for the server tool layer (src/question_bank/server.py)."""

import pytest

from src.question_bank import database as db
from src.question_bank import server


# ── helpers ──────────────────────────────────────────────────

def _seed_bank(bank_id="bank-0001"):
    """Create a bank directly in the DB so server tools can reference it."""
    db.create_question_bank(bank_id, "Algebra I", "Math")
    return bank_id


def _seed_topic(bank_id="bank-0001", topic_id="topic-0001"):
    db.create_topic(topic_id, bank_id, "Linear Equations")
    return topic_id


def _seed_question(bank_id="bank-0001", question_id="q-0001"):
    db.create_question(
        question_id, bank_id,
        question_type="multiple_choice",
        stem="What is 2+2?",
        correct_answer="4",
        options=["3", "4", "5", "6"],
        difficulty=0.3,
        bloom_level="remember",
    )
    return question_id


# ── create_question_bank ─────────────────────────────────────

class TestCreateQuestionBank:
    def test_happy_path(self):
        result = server.create_question_bank("Test Bank", "Science")
        assert "✅" in result
        assert "Test Bank" in result

    def test_with_optional_fields(self):
        result = server.create_question_bank(
            "Bio", "Science", description="Biology bank", grade_level="10th"
        )
        assert "Bio" in result
        assert "10th" in result


# ── list_question_banks ──────────────────────────────────────

class TestListQuestionBanks:
    def test_empty(self):
        result = server.list_question_banks()
        assert "No question banks" in result

    def test_with_banks(self):
        _seed_bank()
        result = server.list_question_banks()
        assert "Algebra I" in result


# ── delete_question_bank ─────────────────────────────────────

class TestDeleteQuestionBank:
    def test_success(self):
        _seed_bank()
        result = server.delete_question_bank("bank-0001")
        assert "✅" in result
        assert "deleted" in result.lower()

    def test_not_found(self):
        result = server.delete_question_bank("bank-nope")
        assert "not found" in result.lower()


# ── get_bank_statistics ──────────────────────────────────────

class TestGetBankStatistics:
    def test_not_found(self):
        result = server.get_bank_statistics("bank-nope")
        assert "not found" in result.lower()

    def test_happy_path(self):
        _seed_bank()
        _seed_question()
        result = server.get_bank_statistics("bank-0001")
        assert "Total Questions" in result


# ── create_topic ─────────────────────────────────────────────

class TestCreateTopic:
    def test_happy_path(self):
        _seed_bank()
        result = server.create_topic("bank-0001", "Quadratics")
        assert "✅" in result
        assert "Quadratics" in result

    def test_bank_not_found(self):
        result = server.create_topic("bank-nope", "X")
        assert "not found" in result.lower()


# ── list_topics ──────────────────────────────────────────────

class TestListTopics:
    def test_empty(self):
        _seed_bank()
        result = server.list_topics("bank-0001")
        assert "No topics" in result

    def test_with_topics(self):
        _seed_bank()
        _seed_topic()
        result = server.list_topics("bank-0001")
        assert "Linear Equations" in result

    def test_bank_not_found(self):
        result = server.list_topics("bank-nope")
        assert "not found" in result.lower()


# ── delete_topic ─────────────────────────────────────────────

class TestDeleteTopic:
    def test_success(self):
        _seed_bank()
        _seed_topic()
        result = server.delete_topic("bank-0001", "topic-0001")
        assert "✅" in result

    def test_bank_not_found(self):
        result = server.delete_topic("bank-nope", "topic-0001")
        assert "not found" in result.lower()

    def test_topic_not_in_bank(self):
        _seed_bank()
        result = server.delete_topic("bank-0001", "topic-nope")
        assert "not found" in result.lower()


# ── create_question — validation ─────────────────────────────

class TestCreateQuestionValidation:
    @pytest.fixture(autouse=True)
    def _bank(self):
        _seed_bank()

    def test_invalid_question_type(self):
        result = server.create_question("bank-0001", "quiz", "Q?", "A")
        assert "Invalid question type" in result

    def test_invalid_bloom_level(self):
        result = server.create_question(
            "bank-0001", "short_answer", "Q?", "A", bloom_level="memorize"
        )
        assert "Invalid Bloom" in result

    def test_mc_without_options(self):
        result = server.create_question("bank-0001", "multiple_choice", "Q?", "A")
        assert "require options" in result.lower()

    def test_difficulty_out_of_range(self):
        result = server.create_question(
            "bank-0001", "short_answer", "Q?", "A", difficulty=1.5
        )
        assert "Difficulty" in result

    def test_negative_points(self):
        result = server.create_question(
            "bank-0001", "short_answer", "Q?", "A", points=-1
        )
        assert "Points" in result

    def test_time_less_than_1(self):
        result = server.create_question(
            "bank-0001", "short_answer", "Q?", "A", estimated_time_seconds=0
        )
        assert "time" in result.lower()

    def test_bank_not_found(self):
        result = server.create_question("bank-nope", "short_answer", "Q?", "A")
        assert "not found" in result.lower()


# ── create_question — happy path ─────────────────────────────

class TestCreateQuestionHappy:
    def test_creates_and_formats(self):
        _seed_bank()
        result = server.create_question(
            "bank-0001", "multiple_choice", "What is 1+1?", "2",
            options=["1", "2", "3"], bloom_level="remember",
        )
        assert "What is 1+1?" in result
        assert "Multiple Choice" in result


# ── get_question ─────────────────────────────────────────────

class TestGetQuestion:
    def test_not_found(self):
        result = server.get_question("q-nope")
        assert "not found" in result.lower()

    def test_show_answer_true(self):
        _seed_bank()
        _seed_question()
        result = server.get_question("q-0001", show_answer=True)
        assert "Correct Answer" in result
        assert "4" in result

    def test_show_answer_false(self):
        _seed_bank()
        _seed_question()
        result = server.get_question("q-0001", show_answer=False)
        assert "Correct Answer" not in result


# ── update_question ──────────────────────────────────────────

class TestUpdateQuestion:
    @pytest.fixture(autouse=True)
    def _setup(self):
        _seed_bank()
        _seed_question()

    def test_not_found(self):
        result = server.update_question("q-nope", stem="X")
        assert "not found" in result.lower()

    def test_no_updates(self):
        result = server.update_question("q-0001")
        assert "No updates" in result

    def test_invalid_bloom(self):
        result = server.update_question("q-0001", bloom_level="memorize")
        assert "Invalid Bloom" in result

    def test_invalid_status(self):
        result = server.update_question("q-0001", status="published")
        assert "Invalid status" in result

    def test_difficulty_out_of_range(self):
        result = server.update_question("q-0001", difficulty=-0.1)
        assert "Difficulty" in result

    def test_negative_points(self):
        result = server.update_question("q-0001", points=-5)
        assert "Points" in result

    def test_time_less_than_1(self):
        result = server.update_question("q-0001", estimated_time_seconds=0)
        assert "time" in result.lower()

    def test_happy_path(self):
        result = server.update_question("q-0001", stem="Updated?")
        assert "✅" in result
        assert "Updated?" in result


# ── delete_question ──────────────────────────────────────────

class TestDeleteQuestion:
    def test_not_found(self):
        result = server.delete_question("q-nope")
        assert "not found" in result.lower()

    def test_success(self):
        _seed_bank()
        _seed_question()
        result = server.delete_question("q-0001")
        assert "✅" in result


# ── search_questions ─────────────────────────────────────────

class TestSearchQuestions:
    def test_no_results(self):
        result = server.search_questions(bank_id="bank-nope")
        assert "No questions found" in result

    def test_returns_results(self):
        _seed_bank()
        _seed_question()
        result = server.search_questions(bank_id="bank-0001")
        assert "Found 1" in result

    def test_limit_clamped_low(self):
        _seed_bank()
        _seed_question()
        # limit=0 should be clamped to 1
        result = server.search_questions(bank_id="bank-0001", limit=0)
        assert "Found" in result

    def test_limit_clamped_high(self):
        _seed_bank()
        _seed_question()
        # limit=999 should be clamped to 100 — still returns the 1 question
        result = server.search_questions(bank_id="bank-0001", limit=999)
        assert "Found 1" in result


# ── activate_questions ───────────────────────────────────────

class TestActivateQuestions:
    def test_activate_draft(self):
        _seed_bank()
        _seed_question()
        result = server.activate_questions(["q-0001"])
        assert "Activated 1" in result

    def test_already_active(self):
        _seed_bank()
        _seed_question()
        db.update_question("q-0001", status="active")
        result = server.activate_questions(["q-0001"])
        assert "already active" in result

    def test_not_found(self):
        result = server.activate_questions(["q-nope"])
        assert "not found" in result

    def test_mixed(self):
        _seed_bank()
        _seed_question("bank-0001", "q-a")
        _seed_question("bank-0001", "q-b")
        db.update_question("q-b", status="active")
        result = server.activate_questions(["q-a", "q-b", "q-nope"])
        assert "Activated 1" in result
        assert "already active" in result
        assert "not found" in result


# ── suggest_questions ────────────────────────────────────────

class TestSuggestQuestions:
    def test_bank_not_found(self):
        result = server.suggest_questions("bank-nope", "Algebra")
        assert "not found" in result.lower()

    def test_returns_suggestions(self):
        _seed_bank()
        result = server.suggest_questions("bank-0001", "Quadratics", count=3)
        assert "Suggestion 1" in result
        assert "Suggestion 3" in result

    def test_bloom_levels_filter(self):
        _seed_bank()
        result = server.suggest_questions(
            "bank-0001", "Topic", bloom_levels=["analyze", "evaluate"]
        )
        assert "Analyze" in result or "analyze" in result.lower()

    def test_difficulty_easy(self):
        _seed_bank()
        result = server.suggest_questions("bank-0001", "X", difficulty="easy")
        assert "0.3" in result
