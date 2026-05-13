from assist.schemas.models import (
    AgentOutput,
    TaskInput,
)


def test_task_input_creation():
    task = TaskInput(
        command="review",
        file_path="main.py",
    )

    assert task.command == "review"
    assert task.language == "python"


def test_agent_output_quality_range():
    output = AgentOutput(
        content="print('hello')",
        agent_name="GeneratorAgent",
        task_type="generate",
        quality_score=0.95,
        iterations_used=1,
    )

    assert output.quality_score == 0.95