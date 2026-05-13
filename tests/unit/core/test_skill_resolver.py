import pytest

from assist.core.skill_resolver import (
    SkillNotFoundError,
    SkillResolver,
)


def test_load_existing_skill():
    resolver = SkillResolver()

    skills = resolver.load(
        ["project_rules"]
    )

    assert len(skills) == 1
    assert skills[0].name == "project_rules"


def test_missing_skill_raises():
    resolver = SkillResolver()

    with pytest.raises(SkillNotFoundError):
        resolver.load(
            ["missing_skill"]
        )