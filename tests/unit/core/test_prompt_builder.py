from assist.core.prompt_builder import PromptBuilder
from assist.schemas.models import Skill, TaskInput


def test_build_review_prompt_includes_code():
    task = TaskInput(
        command="review",
        file_path="test.py",
        raw_input="print('hello')",
    )

    skills = [
        Skill(
            name="project_rules",
            content="Always write clean code.",
        )
    ]

    prompt = PromptBuilder.build_review_prompt(
        task=task,
        skills=skills,
    )

    assert "print('hello')" in prompt
    assert "Always write clean code." in prompt