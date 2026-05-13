import typer

from assist.schemas.models import TaskInput
from assist.agents.reviewer import ReviewerAgent
from assist.llm.mock_client import MockLLMClient

from assist.cli.commands import (
    explain_command,
    generate_command,
    refactor_command,
    review_command,
)

app = typer.Typer(
    help="Assist CLI — Modular AI Coding Assistant",
    no_args_is_help=True,
)

app.command(name="generate")(generate_command)
app.command(name="review")(review_command)
app.command(name="refactor")(refactor_command)
app.command(name="explain")(explain_command)


if __name__ == "__main__":
    app()