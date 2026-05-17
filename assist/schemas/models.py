from typing import Literal

from pydantic import BaseModel, Field


class Issue(BaseModel):
    severity: Literal[
        "critical",
        "high",
        "medium",
        "low",
    ]
    message: str
    location: str | None = None


class Skill(BaseModel):
    name: str
    content: str


class TaskInput(BaseModel):
    command: str
    file_path: str | None = None
    language: str = "python"
    raw_input: str | None = None
    options: dict = Field(default_factory=dict)
    git_range: str | None = None
    repo_path: str | None = None


class ValidationReport(BaseModel):
    is_valid: bool
    quality_score: float = Field(ge=0.0, le=1.0)
    clarity_score: float = Field(ge=0.0, le=1.0)
    issues: list[Issue] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class AgentOutput(BaseModel):
    content: str
    agent_name: str
    task_type: str
    quality_score: float = Field(ge=0.0, le=1.0)
    iterations_used: int = Field(ge=1)


class VerificationResult(BaseModel):
    passed: bool
    syntax_ok: bool
    coherent_with_task: bool
    format_ok: bool
    warnings: list[str] = Field(default_factory=list)
    fatal_issues: list[str] = Field(default_factory=list)


class RegistryResult(BaseModel):
    agent: str
    skills: list[str]


class FileMetadata(BaseModel):
    path: str
    size_bytes: int
    lines: int


class ProjectFileNode(BaseModel):
    path: str
    module: str
    imports: list[str] = Field(default_factory=list)
    imported_by: list[str] = Field(default_factory=list)
    size_bytes: int
    lines: int


class ProjectGraph(BaseModel):
    root: str
    files: list[ProjectFileNode] = Field(default_factory=list)


class ProjectContextFile(BaseModel):
    path: str
    module: str
    importance_score: float = Field(ge=0.0, le=1.0)
    imports: list[str] = Field(default_factory=list)
    imported_by: list[str] = Field(default_factory=list)


class ProjectContext(BaseModel):
    root: str
    summary: str
    total_files: int
    entry_points: list[str] = Field(default_factory=list)
    primary_files: list[ProjectContextFile] = Field(default_factory=list)


class ArchitectureReport(BaseModel):
    has_cycles: bool
    cycles: list[list[str]] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)


class RepositoryHealthReport(BaseModel):
    total_files: int
    total_dependencies: int
    cyclic_dependencies: int
    highly_connected_files: list[str] = Field(default_factory=list)
    health_score: float = Field(ge=0.0, le=1.0)
    issues: list[Issue] = Field(default_factory=list)


class FunctionInfo(BaseModel):
    name: str
    line_count: int = 0
    complexity: int = 1
    lineno: int = 0
    end_lineno: int | None = None
    decorators: list[str] = Field(default_factory=list)


class ClassInfo(BaseModel):
    name: str
    lineno: int = 0
    end_lineno: int | None = None
    methods: list[FunctionInfo] = Field(default_factory=list)


class SemanticAnalysis(BaseModel):
    path: str = ""
    functions: list[FunctionInfo] = Field(default_factory=list)
    classes: list[ClassInfo] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    calls: list[str] = Field(default_factory=list)


class CrossFileReference(BaseModel):
    source_file: str
    target_file: str
    symbol: str


class CrossFileAnalysis(BaseModel):
    imports: list[CrossFileReference] = Field(default_factory=list)
    function_calls: list[CrossFileReference] = Field(default_factory=list)


class ArchitecturalRisk(BaseModel):
    risk_type: str
    severity: str
    file: str
    description: str


class ArchitecturalRiskReport(BaseModel):
    risks: list[ArchitecturalRisk] = Field(default_factory=list)


class GodClassFinding(BaseModel):
    class_name: str
    method_count: int
    severity: str
    recommendation: str


class GodClassReport(BaseModel):
    findings: list[GodClassFinding] = Field(default_factory=list)


class LongMethodFinding(BaseModel):
    function_name: str
    line_count: int
    severity: str
    recommendation: str


class LongMethodReport(BaseModel):
    findings: list[LongMethodFinding] = Field(default_factory=list)


class CodeQualityReport(BaseModel):
    complexity_warnings: list[str] = Field(default_factory=list)
    dead_functions: list[str] = Field(default_factory=list)
    architectural_risks: list[str] = Field(default_factory=list)
    long_methods: list[str] = Field(default_factory=list)
    god_classes: list[str] = Field(default_factory=list)


FunctionSymbol = FunctionInfo
ClassSymbol = ClassInfo
SemanticFileAnalysis = SemanticAnalysis

class PromptContext(BaseModel):
    file_path: str = ""
    file_metadata: dict = Field(default_factory=dict)
    repository_context: dict = Field(default_factory=dict)
    architecture_context: dict = Field(default_factory=dict)
    semantic_context: dict = Field(default_factory=dict)
    cross_file_context: dict = Field(default_factory=dict)
    risk_context: dict = Field(default_factory=dict)
    code_quality_context: dict = Field(default_factory=dict)

class FinalOutput(BaseModel):
    raw_content: str
    verification: VerificationResult
    agent_name: str
    task_type: str
    quality_score: float = Field(ge=0.0, le=1.0)
    iterations_used: int = Field(ge=1, default=1)

class FileDiff(BaseModel):
    """Diff di un singolo file modificato dal range git.

    Rappresenta cosa e' cambiato in un file specifico:
    quante righe aggiunte/rimosse e l'output testuale del diff
    per quel file (sezione "hunks").
    """

    path: str

    additions: int = 0

    deletions: int = 0

    hunks: str = ""


class GitDiff(BaseModel):
    """Risultato dell'estrazione di un diff git su un range.

    Aggrega tutti i FileDiff prodotti dal range specificato,
    piu' metadati aggregati (summary) e l'output raw di git diff
    (utile per il prompt completo da inviare all'LLM).
    """

    range_spec: str

    files: list[FileDiff] = []

    files_changed: int = 0

    total_additions: int = 0

    total_deletions: int = 0

    raw_diff: str = ""