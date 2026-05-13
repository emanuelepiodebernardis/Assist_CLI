import ast

from assist.agents.explainer import ExplainerAgent
from assist.agents.generator import GeneratorAgent
from assist.agents.refactor import RefactorAgent
from assist.agents.reviewer import ReviewerAgent

from assist.core.assembler import ResponseAssembler
from assist.core.context_guard import ContextGuard
from assist.core.project_scanner import ProjectScanner
from assist.core.registry import Registry

from assist.core.repository_context import (
    RepositoryContextBuilder,
)

from assist.core.skill_resolver import (
    SkillResolver,
)

from assist.core.verifier import GlobalVerifier

from assist.core.architecture_analyzer import (
    ArchitectureAnalyzer,
)

from assist.core.project_graph import (
    ProjectGraphBuilder,
)

from assist.core.repository_health import (
    RepositoryHealthAnalyzer,
)

from assist.core.architectural_risk_analyzer import (
    ArchitecturalRiskAnalyzer,
)

from assist.core.semantic_analyzer import (
    SemanticAnalyzer,
)

from assist.core.cross_file_analyzer import (
    CrossFileAnalyzer,
)

from assist.core.code_quality_analyzer import (
    CodeQualityAnalyzer,
)

from assist.llm.factory import LLMFactory

from assist.schemas.models import (
    TaskInput,
)

from assist.utils.file_metadata import (
    build_file_metadata,
)

from assist.utils.file_reader import (
    FileReader,
)


MAX_CORRECTIONS_PER_AGENT: dict[str, int] = {
    "ReviewerAgent": 1,
    "GeneratorAgent": 2,
    "RefactorAgent": 2,
    "ExplainerAgent": 1,
}


DEFAULT_MAX_CORRECTIONS: int = 1


class Orchestrator:

    def __init__(self) -> None:

        self.registry = Registry()

        self.skill_resolver = SkillResolver()

        self.verifier = GlobalVerifier()

        self.assembler = ResponseAssembler()

    def _build_agent(
        self,
        agent_name: str,
    ):

        llm = LLMFactory.create(
            provider="anthropic",
        )

        agents = {
            "GeneratorAgent": GeneratorAgent,
            "ReviewerAgent": ReviewerAgent,
            "RefactorAgent": RefactorAgent,
            "ExplainerAgent": ExplainerAgent,
        }

        agent_class = agents[agent_name]

        max_corrections = (
            MAX_CORRECTIONS_PER_AGENT.get(
                agent_name,
                DEFAULT_MAX_CORRECTIONS,
            )
        )

        return agent_class(
            llm=llm,
            max_corrections=max_corrections,
        )

    def run(
        self,
        task: TaskInput,
    ) -> str:

        agent_name, skills = (
            self.registry.resolve(
                task.command
            )
        )

        loaded_skills = (
            self.skill_resolver.load(
                skills
            )
        )

        file_content = ""

        metadata_dump: dict = {}

        repository_context: dict = {}

        semantic_context: dict = {}

        architecture_context: dict = {}

        cross_file_context: dict = {}

        risk_context: dict = {}

        code_quality_context: dict = {}

        if task.file_path:

            raw_content = (
                FileReader.read(
                    task.file_path
                )
            )

            file_content = (
                ContextGuard.validate(
                    raw_content
                )
            )

            metadata = (
                build_file_metadata(
                    task.file_path,
                    raw_content,
                )
            )

            metadata_dump = metadata.model_dump()

            tree = ast.parse(raw_content)

            project_files = (
                ProjectScanner()
                .scan(".")
            )

            repository_context = (
                RepositoryContextBuilder()
                .build(
                    task.file_path,
                    project_files,
                )
            )

            graph = (
                ProjectGraphBuilder()
                .build(".")
            )

            architecture_report = (
                ArchitectureAnalyzer()
                .detect_cycles(
                    graph
                )
            )

            health_report = (
                RepositoryHealthAnalyzer()
                .analyze(
                    graph=graph,
                    cycles=(
                        architecture_report.cycles
                    ),
                )
            )

            risk_report = (
                ArchitecturalRiskAnalyzer()
                .analyze(graph)
            )

            semantic = (
                SemanticAnalyzer()
                .analyze_file(
                    task.file_path
                )
            )

            quality_report = (
                CodeQualityAnalyzer()
                .analyze(
                    semantic=semantic,
                    graph=graph,
                    tree=tree,
                )
            )

            semantic_context = {
                "functions": [
                    function.name
                    for function in (
                        semantic.functions
                    )
                ],
                "classes": [
                    class_.name
                    for class_ in (
                        semantic.classes
                    )
                ],
                "imports": (
                    semantic.imports
                ),
                "calls": (
                    semantic.calls
                ),
            }

            cross_analysis = (
                CrossFileAnalyzer()
                .analyze(project_files)
            )

            cross_file_context = {
                "imports": [
                    {
                        "source": (
                            ref.source_file
                        ),
                        "target": (
                            ref.target_file
                        ),
                        "symbol": (
                            ref.symbol
                        ),
                    }
                    for ref in (
                        cross_analysis.imports
                    )
                ],
                "function_calls": [
                    {
                        "source": (
                            ref.source_file
                        ),
                        "target": (
                            ref.target_file
                        ),
                        "symbol": (
                            ref.symbol
                        ),
                    }
                    for ref in (
                        cross_analysis.function_calls
                    )
                ],
            }

            architecture_context = {
                "cyclic_dependencies": (
                    architecture_report.cycles
                ),
                "highly_connected_files": (
                    health_report
                    .highly_connected_files
                ),
                "health_score": (
                    health_report
                    .health_score
                ),
            }

            risk_context = {
                "risks": [
                    {
                        "type": (
                            risk.risk_type
                        ),
                        "severity": (
                            risk.severity
                        ),
                        "file": (
                            risk.file
                        ),
                        "description": (
                            risk.description
                        ),
                    }
                    for risk in (
                        risk_report.risks
                    )
                ]
            }

            code_quality_context = (
                quality_report.model_dump()
            )

        task_with_context = (
            task.model_copy(
                update={
                    "raw_input": (
                        file_content
                    ),
                    "options": {
                        **task.options,
                        "metadata": (
                            metadata_dump
                        ),
                        "repository_context": (
                            repository_context
                        ),
                        "architecture_context": (
                            architecture_context
                        ),
                        "semantic_context": (
                            semantic_context
                        ),
                        "cross_file_context": (
                            cross_file_context
                        ),
                        "risk_context": (
                            risk_context
                        ),
                        "code_quality_context": (
                            code_quality_context
                        ),
                    },
                }
            )
        )

        agent = self._build_agent(
            agent_name
        )

        output = agent.run(
            task=task_with_context,
            skills=loaded_skills,
        )

        verification = (
            self.verifier.check(
                output
            )
        )

        return self.assembler.build(
            output,
            verification,
        )