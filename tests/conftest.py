"""Test fixtures for CareerMilestoneTracker."""

import tempfile
import os

import pytest

from main import app


@pytest.fixture
def test_app(tmp_path):
    """Create app with a temporary database."""
    db_path = tmp_path / "test.db"
    app.config["DB_PATH"] = str(db_path)
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def client(test_app):
    """Flask test client."""
    return test_app.test_client()


@pytest.fixture
def seed_milestones(client):
    """Add sample milestones for testing."""
    milestones = [
        {"title": "Senior Engineer", "date": "2024-01-15", "category": "promotion", "description": "Promoted to senior"},
        {"title": "AWS Solutions Architect", "date": "2024-03-20", "category": "certification", "description": ""},
        {"title": "Auth Service Rewrite", "date": "2023-11-01", "category": "project", "description": "Led the rewrite"},
        {"title": "Employee of the Year", "date": "2024-06-01", "category": "award", "description": "Annual award"},
        {"title": "PyCon Talk", "date": "2023-09-15", "category": "talk", "description": "Spoke about testing"},
    ]
    for m in milestones:
        client.post("/add", data=m, follow_redirects=True)
    return milestones
