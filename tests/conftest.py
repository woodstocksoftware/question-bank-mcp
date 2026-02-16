"""Shared fixtures for question bank tests."""

import pytest
from pathlib import Path

from src.question_bank import database as db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Give every test its own empty SQLite database."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DATABASE_PATH", test_db)
    db.init_database()
    yield test_db
