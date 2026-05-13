from __future__ import annotations

from pathlib import Path

import pytest

from assist.core.architecture_analyzer import ArchitectureAnalyzer
from assist.core.code_quality_analyzer import CodeQualityAnalyzer
from assist.core.orchestrator import Orchestrator
from assist.core.project_scanner import ProjectScanner
from assist.core.project_graph import ProjectGraphBuilder
from assist.core.repository_context import RepositoryContextBuilder
from assist.core.repository_health import RepositoryHealthAnalyzer
from assist.core.semantic_analyzer import SemanticAnalyzer
from assist.llm.factory import LLMFactory
from assist.schemas.models import (
    ArchitectureReport,
    CodeQualityReport,
    FileMetadata,
    FunctionInfo,
    ProjectFileNode,
    ProjectGraph,
    RepositoryHealthReport,
    SemanticAnalysis,
)


REVIEW_DRAFT_GENERIC = (
    "## Sommario\n\n"
    "Il file contiene problemi di stile "
    "e una credenziale hardcoded.\n"
)


SELF_CHECK_INVALID_JSON = (
    "{\n"
    '  "is_valid": false,\n'
    '  "quality_score": 0.45,\n'
    '  "clarity_score": 0.60,\n'
    '  "issues": [\n'
    "    {\n"
    '      "severity": "medium",\n'
    '      "message": "La review e troppo generica.",\n'
    '      "location": null\n'
    "    }\n"
    "  ],\n"
    '  "actions": [\n'
    '    "Aggiungere dettagli specifici sui problemi.",\n'
    '    "Migliorare la sezione dei fix."\n'
    "  ]\n"
    "}\n"
)


REVIEW_DRAFT_CORRECTED = (
    "## Sommario\n\n"
    "Il file `sample.py` contiene una funzione semplice ma presenta "
    "problemi di stile e una credenziale hardcoded.\n\n"
    "## Problemi critici\n"
    '- `password = "12345"` espone una credenziale in chiaro.\n\n'
    "## Problemi significativi\n"
    "- L'indentazione e incoerente.\n"
    "- Mancano type hints.\n"
    "- La chiamata `print(add(1,2))` non e formattata secondo PEP 8.\n\n"
    "## Suggerimenti\n"
    "- Usare `APP_PASSWORD` da variabili d'ambiente.\n"
    "- Aggiungere type hints e docstring.\n"
    "- Correggere spaziatura e indentazione.\n"
)


SELF_CHECK_VALID_JSON = (
    "{\n"
    '  "is_valid": true,\n'
    '  "quality_score": 0.88,\n'
    '  "clarity_score": 0.90,\n'
    '  "issues": [],\n'
    '  "actions": []\n'
    "}\n"
)


class SequencedMockLLM:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str, system: str = "") -> str:
        self.prompts.append(prompt)

        if not self._responses:
            raise AssertionError(
                "LLM called more times than expected. "
                f"Total prompts received: {len(self.prompts)}"
            )

        return self._responses.pop(0)


def test_review_flow_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):

    sample_file = tmp_path / "sample.py"

    sample_file.write_text(
        'def add(a, b):\n'
        ' return a+b\n'
        '\n'
        'password = "12345"\n'
        '\n'
        'print(add(1,2))\n',
        encoding="utf-8",
    )

    llm = SequencedMockLLM(
        responses=[
            REVIEW_DRAFT_GENERIC,
            SELF_CHECK_INVALID_JSON,
            REVIEW_DRAFT_CORRECTED,
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
                path=str(sample_file),
                size_bytes=sample_file.stat().st_size,
                lines=len(
                    sample_file
                    .read_text(encoding="utf-8")
                    .splitlines()
                ),
            )
        ],
    )

    monkeypatch.setattr(
        RepositoryContextBuilder,
        "build",
        lambda self, target_file, project_files: {
            "related_files": [str(sample_file)],
            "project_size": len(project_files),
        },
    )

    monkeypatch.setattr(
        ProjectGraphBuilder,
        "build",
        lambda self, root: ProjectGraph(
            root=str(root),
            files=[
                ProjectFileNode(
                    path=str(sample_file),
                    module="sample",
                    imports=[],
                    imported_by=[],
                    size_bytes=sample_file.stat().st_size,
                    lines=len(
                        sample_file
                        .read_text(encoding="utf-8")
                        .splitlines()
                    ),
                )
            ],
        ),
    )

    monkeypatch.setattr(
        ArchitectureAnalyzer,
        "detect_cycles",
        lambda self, graph: ArchitectureReport(
            has_cycles=False,
            cycles=[],
            issues=[],
        ),
    )

    monkeypatch.setattr(
        RepositoryHealthAnalyzer,
        "analyze",
        lambda self, graph, cycles: RepositoryHealthReport(
            total_files=len(graph.files),
            total_dependencies=0,
            cyclic_dependencies=len(cycles),
            highly_connected_files=[],
            health_score=0.92,
            issues=[],
        ),
    )

    monkeypatch.setattr(
        SemanticAnalyzer,
        "analyze_file",
        lambda self, file_path: SemanticAnalysis(
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
            calls=["print"],
        ),
    )

    monkeypatch.setattr(
        CodeQualityAnalyzer,
        "analyze",
        lambda self, semantic, graph, tree=None: (
            CodeQualityReport(
                complexity_warnings=[],
                dead_functions=[],
                architectural_risks=[],
                long_methods=[],
                god_classes=[],
            )
        ),
    )

    orchestrator = Orchestrator()

    result = orchestrator.run(
        task=(
            orchestrator.registry.task_model(
                command="review",
                file_path=str(sample_file),
            )
            if hasattr(
                orchestrator.registry,
                "task_model",
            )
            else __import__(
                "assist.schemas.models",
                fromlist=["TaskInput"],
            ).TaskInput(
                command="review",
                file_path=str(sample_file),
            )
        )
    )

    assert result.task_type == "review"

    assert result.agent_name == "ReviewerAgent"

    assert "## Sommario" in result.raw_content

    assert (
        "Problemi critici"
        in result.raw_content
    )

    assert len(llm.prompts) == 4

    assert (
        "CONTESTO STRUTTURALE DEL PROGETTO"
        in llm.prompts[0]
    )

    assert (
        'password = "12345"'
        in llm.prompts[0]
    )

    assert isinstance(
        result.quality_score,
        float,
    )

    assert result.quality_score == pytest.approx(0.88)