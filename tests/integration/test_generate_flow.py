from __future__ import annotations

from pathlib import Path

import pytest

from assist.core.architecture_analyzer import (
    ArchitectureAnalyzer,
)
from assist.core.code_quality_analyzer import (
    CodeQualityAnalyzer,
)
from assist.core.orchestrator import (
    Orchestrator,
)
from assist.core.project_graph import (
    ProjectGraphBuilder,
)
from assist.core.project_scanner import (
    ProjectScanner,
)
from assist.core.repository_context import (
    RepositoryContextBuilder,
)
from assist.core.repository_health import (
    RepositoryHealthAnalyzer,
)
from assist.core.semantic_analyzer import (
    SemanticAnalyzer,
)
from assist.llm.factory import (
    LLMFactory,
)
from assist.schemas.models import (
    ArchitectureReport,
    CodeQualityReport,
    FileMetadata,
    FinalOutput,
    FunctionInfo,
    ProjectFileNode,
    ProjectGraph,
    RepositoryHealthReport,
    SemanticAnalysis,
)


DRAFT_INCOMPLETE = (
    "def add(a, b):\n"
    "    return a + b\n"
)


SELF_CHECK_INVALID_JSON = (
    "{\n"
    '  "is_valid": false,\n'
    '  "quality_score": 0.45,\n'
    '  "clarity_score": 0.60,\n'
    '  "issues": [\n'
    "    {\n"
    '      "severity": "medium",\n'
    '      "message": "Missing type hints and docstring.",\n'
    '      "location": "line 1"\n'
    "    }\n"
    "  ],\n"
    '  "actions": [\n'
    '    "Add type hints",\n'
    '    "Add docstring"\n'
    "  ]\n"
    "}\n"
)


DRAFT_CORRECTED = (
    "def add(a: int, b: int) -> int:\n"
    '    """Add two integers.\n'
    "\n"
    "    Args:\n"
    "        a: First integer.\n"
    "        b: Second integer.\n"
    "\n"
    "    Returns:\n"
    "        Sum of a and b.\n"
    '    """\n'
    "    return a + b\n"
)


SELF_CHECK_VALID_JSON = (
    "{\n"
    '  "is_valid": true,\n'
    '  "quality_score": 0.91,\n'
    '  "clarity_score": 0.90,\n'
    '  "issues": [],\n'
    '  "actions": []\n'
    "}\n"
)


class SequencedMockLLM:

    def __init__(
        self,
        responses: list[str],
    ) -> None:

        self._responses = list(
            responses
        )

        self.prompts: list[str] = []

    def complete(
        self,
        prompt: str,
        system: str = "",
    ) -> str:

        self.prompts.append(
            prompt
        )

        if not self._responses:
            raise AssertionError(
                "LLM called more times than expected. "
                f"Total prompts received: {len(self.prompts)}"
            )

        return self._responses.pop(0)


def test_generate_flow_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):

    target_file = (
        tmp_path
        / "generated_math.py"
    )

    target_file.write_text(
        "",
        encoding="utf-8",
    )

    llm = SequencedMockLLM(
        responses=[
            DRAFT_INCOMPLETE,
            SELF_CHECK_INVALID_JSON,
            DRAFT_CORRECTED,
            SELF_CHECK_VALID_JSON,
        ]
    )

    monkeypatch.setattr(
        LLMFactory,
        "create",
        lambda provider="anthropic": llm,
    )

    monkeypatch.setattr(
        ProjectScanner,
        "scan",
        lambda self, root: [
            FileMetadata(
                path=str(
                    target_file
                ),
                size_bytes=0,
                lines=0,
            )
        ],
    )

    monkeypatch.setattr(
        RepositoryContextBuilder,
        "build",
        lambda self,
        target_file,
        project_files: {
            "related_files": [],
            "project_size": len(
                project_files
            ),
        },
    )

    monkeypatch.setattr(
        ProjectGraphBuilder,
        "build",
        lambda self,
        root: ProjectGraph(
            root=str(root),
            files=[
                ProjectFileNode(
                    path=str(
                        target_file
                    ),
                    module="generated_math",
                    imports=[],
                    imported_by=[],
                    size_bytes=0,
                    lines=0,
                )
            ],
        ),
    )

    monkeypatch.setattr(
        ArchitectureAnalyzer,
        "detect_cycles",
        lambda self,
        graph: ArchitectureReport(
            has_cycles=False,
            cycles=[],
            issues=[],
        ),
    )

    monkeypatch.setattr(
        RepositoryHealthAnalyzer,
        "analyze",
        lambda self,
        graph,
        cycles: RepositoryHealthReport(
            total_files=len(
                graph.files
            ),
            total_dependencies=0,
            cyclic_dependencies=0,
            highly_connected_files=[],
            health_score=1.0,
            issues=[],
        ),
    )

    monkeypatch.setattr(
        SemanticAnalyzer,
        "analyze_file",
        lambda self,
        file_path: SemanticAnalysis(
            path=file_path,
            functions=[
                FunctionInfo(
                    name="add",
                    line_count=2,
                    complexity=1,
                    lineno=1,
                    end_lineno=2,
                )
            ],
            classes=[],
            imports=[],
            calls=[],
        ),
    )

    monkeypatch.setattr(
        CodeQualityAnalyzer,
        "analyze",
        lambda self,
        semantic,
        graph,
        tree=None: CodeQualityReport(
            complexity_warnings=[],
            dead_functions=[],
            architectural_risks=[],
            long_methods=[],
            god_classes=[],
        ),
    )

    orchestrator = (
        Orchestrator()
    )

    task_model = (
        orchestrator.registry.task_model
        if hasattr(
            orchestrator.registry,
            "task_model",
        )
        else __import__(
            "assist.schemas.models",
            fromlist=["TaskInput"],
        ).TaskInput
    )

    result = orchestrator.run(
        task=task_model(
            command="generate",
            file_path=str(
                target_file
            ),
            language="python",
            options={
                "prompt": (
                    "Generate a typed "
                    "add function."
                )
            },
        )
    )

    assert isinstance(
        result,
        FinalOutput,
    )

    assert (
        "def add"
        in result.raw_content
    )

    assert (
        "-> int"
        in result.raw_content
    )

    assert (
        '"""Add two integers.'
        in result.raw_content
    )

    assert (
        result.verification.passed
        is True
    )

    assert (
        result.verification.syntax_ok
        is True
    )

    assert (
        result.task_type
        == "generate"
    )

    assert (
        result.agent_name
        == "GeneratorAgent"
    )

    assert (
        len(llm.prompts)
        == 4
    )

    assert (
        result.quality_score
        == pytest.approx(0.91)
    )