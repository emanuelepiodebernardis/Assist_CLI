from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from assist.core.orchestrator import Orchestrator
from assist.core.output_formatter import OutputFormatter
from assist.schemas.models import TaskInput

app = typer.Typer()

console = Console()


def validate_file_exists(
    file_path: str,
) -> None:

    path = Path(file_path)

    if not path.exists():
        raise typer.BadParameter(
            f"File not found: {file_path}"
        )


def _handle_output(
    formatted_output,
    output_format: str,
    output_path: str | None = None,
) -> None:

    if output_path:

        output_file = Path(output_path)

        output_file.write_text(
            str(formatted_output),
            encoding="utf-8",
        )

        typer.echo(
            f"Report saved to: {output_file}"
        )

        return

    if output_format == "terminal":

        console.print(
            formatted_output
        )

    else:

        typer.echo(
            formatted_output
        )


def generate_command(
    file: str,
    prompt: str = "Generate Python code",
    lang: str = "python",
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            help="terminal | markdown | json",
        ),
    ] = "terminal",
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            help="Save output to file",
        ),
    ] = None,
) -> None:

    task = TaskInput(
        command="generate",
        file_path=file,
        language=lang,
        options={
            "prompt": prompt,
        },
    )

    orchestrator = Orchestrator()

    formatter = OutputFormatter()

    result = orchestrator.run(
        task
    )

    formatted_output = (
        formatter.format(
            result,
            format_type=output_format,
        )
    )

    _handle_output(
        formatted_output=formatted_output,
        output_format=output_format,
        output_path=output,
    )


def review_command(
    file: str,
    strict: bool = False,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            help="terminal | markdown | json",
        ),
    ] = "terminal",
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            help="Save output to file",
        ),
    ] = None,
) -> None:

    validate_file_exists(file)

    task = TaskInput(
        command="review",
        file_path=file,
        options={
            "strict": strict,
        },
    )

    orchestrator = Orchestrator()

    formatter = OutputFormatter()

    result = orchestrator.run(
        task
    )

    formatted_output = (
        formatter.format(
            result,
            format_type=output_format,
        )
    )

    _handle_output(
        formatted_output=formatted_output,
        output_format=output_format,
        output_path=output,
    )


def refactor_command(
    file: str,
    target: str = "readability",
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            help="terminal | markdown | json",
        ),
    ] = "terminal",
    output_file: Annotated[
        str | None,
        typer.Option(
            "--output",
            help="Save output to file",
        ),
    ] = None,
) -> None:

    validate_file_exists(file)

    task = TaskInput(
        command="refactor",
        file_path=file,
        options={
            "target": target,
        },
    )

    orchestrator = Orchestrator()

    formatter = OutputFormatter()

    result = orchestrator.run(
        task
    )

    formatted_output = formatter.format(
        result,
        format_type=output_format,
    )

    _handle_output(
        formatted_output=formatted_output,
        output_format=output_format,
        output_path=output_file,
    )


def explain_command(
    file: str,
    depth: str = "brief",
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            help="terminal | markdown | json",
        ),
    ] = "terminal",
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            help="Save output to file",
        ),
    ] = None,
) -> None:

    validate_file_exists(file)

    task = TaskInput(
        command="explain",
        file_path=file,
        options={
            "depth": depth,
        },
    )

    orchestrator = Orchestrator()

    formatter = OutputFormatter()

    result = orchestrator.run(
        task
    )

    formatted_output = (
        formatter.format(
            result,
            format_type=output_format,
        )
    )

    _handle_output(
        formatted_output=formatted_output,
        output_format=output_format,
        output_path=output,
    )