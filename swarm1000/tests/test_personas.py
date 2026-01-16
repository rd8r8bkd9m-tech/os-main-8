"""Tests for persona generation."""

import tempfile
from pathlib import Path

from swarm1000.core.personas import (
    generate_personas,
    load_personas_jsonl,
    save_personas_jsonl,
)


def test_generate_personas_count():
    """Test that correct number of personas are generated."""
    personas = generate_personas(1000)
    assert len(personas) == 1000


def test_generate_personas_ids_unique():
    """Test that persona IDs are unique."""
    personas = generate_personas(100)
    ids = [p.id for p in personas]
    assert len(ids) == len(set(ids))


def test_generate_personas_role_distribution():
    """Test that role distribution is approximately correct."""
    personas = generate_personas(1000)

    # Count by role
    role_counts = {}
    for persona in personas:
        role_counts[persona.role] = role_counts.get(persona.role, 0) + 1

    # Check key roles exist
    assert "PM-Chief" in role_counts
    assert "Backend Engineer" in role_counts
    assert "Frontend Engineer" in role_counts

    # PM-Chief should be 1
    assert role_counts.get("PM-Chief", 0) == 1


def test_persona_has_required_fields():
    """Test that personas have all required fields."""
    personas = generate_personas(10)

    for persona in personas:
        assert persona.id
        assert persona.role
        assert persona.seniority
        assert isinstance(persona.stack, list)
        assert persona.style
        assert isinstance(persona.constraints, list)
        assert isinstance(persona.review_skill, int)
        assert 1 <= persona.review_skill <= 10


def test_save_and_load_personas():
    """Test saving and loading personas to/from JSONL."""
    personas = generate_personas(50)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "personas.jsonl"
        save_personas_jsonl(personas, path)

        assert path.exists()

        loaded = load_personas_jsonl(path)
        assert len(loaded) == len(personas)

        # Check first persona
        assert loaded[0].id == personas[0].id
        assert loaded[0].role == personas[0].role
        assert loaded[0].seniority == personas[0].seniority


def test_review_skill_correlates_with_seniority():
    """Test that review skill is higher for senior personas."""
    personas = generate_personas(100)

    junior_skills = []
    senior_skills = []

    for persona in personas:
        if persona.seniority == "Junior":
            junior_skills.append(persona.review_skill)
        elif persona.seniority in ["Senior", "Staff", "Principal"]:
            senior_skills.append(persona.review_skill)

    if junior_skills and senior_skills:
        avg_junior = sum(junior_skills) / len(junior_skills)
        avg_senior = sum(senior_skills) / len(senior_skills)
        assert avg_senior > avg_junior


def test_custom_count():
    """Test generating custom count of personas."""
    personas = generate_personas(250)
    assert len(personas) == 250

    personas = generate_personas(42)
    assert len(personas) == 42
