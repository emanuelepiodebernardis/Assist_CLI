# Assist CLI

A modular command-line coding assistant for Python that combines deterministic static analysis with LLM agents under declarative skill constraints.

Each command runs through a verifiable pipeline: code analysis produces structural facts about your codebase, skills encode quality rules, and specialized agents produce output that passes a self-validation loop plus a global verification layer before reaching you.

```
50 tests passing in ~3 seconds. Pipeline validated end-to-end with MockLLM.
```

---

## What it does

Four commands, one specialized agent per task:

| Command | Agent | Purpose |
|---------|-------|---------|
| `assist review <file>` | ReviewerAgent | Technical review with concrete fixes |
| `assist generate <file>` | GeneratorAgent | Generate Python code from a text specification |
| `assist refactor <file>` | RefactorAgent | Refactor code while preserving observable behavior |
| `assist explain <file>` | ExplainerAgent | Technical explanation anchored to project context |

Every command produces structured output with:

- A **quality score** (0.0–1.0) computed by a deterministic rubric
- A **verification table** (syntax, format, coherence, fatal issues)
- An **iteration count** showing how many self-correction passes were needed

---

## What it is not

To set the right expectations from the start:

- **Not a chat assistant.** No conversation, no memory between invocations. Each command is an atomic operation with well-defined input and output.
- **Not a generic LLM wrapper.** Every invocation applies structural constraints, declarative skills, and verifiable quality gates.
- **Not a linter.** Static analysis is infrastructure, not output. The final result is always produced by an LLM, under constraints.
- **Not an autonomous agent.** Produces text or code for you to review. Executing changes remains a human decision.

---

## Installation

Requires Python 3.10+ and an Anthropic API key.

```bash
git clone https://github.com/emanuelepiodebernardis/Assist_CLI.git
cd Assist_CLI
pip install -e .
```

Set the API key:

```bash
# Linux / macOS
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

Verify the install:

```bash
assist --help
```

---

## Quick start

### Review a file

```bash
assist review path/to/module.py
```

Produces a technical review with `## Sommario`, `## Problemi critici`, `## Problemi significativi`, `## Suggerimenti`. The review uses static-analysis facts (dead code, cyclic imports, god classes, complexity warnings) to ground itself in real findings rather than generic impressions.

### Explain a file

```bash
assist explain path/to/module.py --depth brief
```

Available depth values: `brief`, `verbose`. The explanation covers purpose, structure, responsibilities, dependencies, and notable critical points — anchored in the project context.

### Refactor a file

```bash
assist refactor path/to/module.py --target readability
```

Strict behavioral-invariance constraint: the refactor cannot change observable behavior. If a bug is found in the original, it is preserved and reported in `## Note`, not silently fixed.

### Generate code

```bash
assist generate output_file.py --prompt "Implement a binary search function for sorted integer lists"
```

Produces pure Python (no markdown fences) ready to be saved.

### Output formats

All four commands accept:

```bash
--format terminal   # Rich rendering (default)
--format markdown   # Raw markdown for piping or saving
--format json       # Structured output for tooling
--output report.md  # Save to file instead of stdout
```

---

## Example: real output

Here's what `assist explain` produced when run on the project's own `verifier.py`:

```
╭───────────────────────╮
│ ASSIST REVIEW RESULT  │
│ Agent: ExplainerAgent │
│ Task: explain         │
│ Quality Score: 0.88   │
│ Iterations: 1         │
╰───────────────────────╯
 Verification Status
┏━━━━━━━━━━━┳━━━━━━━━┓
┃ Check     ┃ Status ┃
┡━━━━━━━━━━━╇━━━━━━━━┩
│ Passed    │ PASS   │
│ Syntax    │ PASS   │
│ Format    │ PASS   │
│ Coherence │ PASS   │
└───────────┴────────┘
```

The body included a section called **Criticità** (Critical points) that identified two real issues:

1. `coherent_with_task` in `VerificationResult` is hardcoded to `True` — the field exists but the verification logic is not implemented.
2. The quality analyzer flags all functions as dead code, likely because `GlobalVerifier` is instantiated dynamically in `orchestrator.py` and the static analyzer can't trace the call.

The first point a pure linter wouldn't find (it's not a formal violation). The second required interpreting the dynamic instantiation pattern, which an LLM without structural context wouldn't produce. The system found both because it combines deterministic analysis with LLM interpretation.

---

## How it works

```
CLI command
   ↓
Orchestrator
   ↓
Static analysis layer (8 analyzers)
   ↓
Registry (resolves agent + skills for the task)
   ↓
Agent
   └─ generate_draft  →  self_check  →  correct  →  self_check  →  ...
   ↓
GlobalVerifier (syntax, non-empty, placeholders, task-aware)
   ↓
OutputFormatter (terminal | markdown | json)
   ↓
You
```

### Static analysis layer

Eight analyzers run on every invocation, producing typed Pydantic reports:

- **ProjectScanner** — file enumeration with metadata
- **ProjectGraphBuilder** — dependency graph at module level
- **ArchitectureAnalyzer** — cyclic dependency detection
- **RepositoryHealthAnalyzer** — overall health score (0.0–1.0)
- **ArchitecturalRiskAnalyzer** — risk classification (fan-out, depth, coupling)
- **SemanticAnalyzer** — functions, classes, imports, calls per file
- **CrossFileAnalyzer** — inter-file imports and function calls
- **CodeQualityAnalyzer** — complexity warnings, dead functions, long methods, god classes

The results are aggregated into a structural context block injected into the LLM prompt.

### Self-validation loop

Each agent inherits from `BaseAgent` and implements three methods: `generate_draft`, `self_check`, `correct`. The base loop:

```
draft = generate_draft()
for iteration in 1..max_corrections+1:
    report = self_check(draft)
    if report.is_valid: break
    if iteration == max_corrections+1: break  # final pass: validate, do not correct
    draft = correct(draft, report)
return AgentOutput(quality_score=report.quality_score, ...)
```

Key property: the `quality_score` always reflects the **final** draft, not an intermediate one. The reported score is honest about what the user actually receives.

`max_corrections` is differentiated per agent: code-producing agents (Generator, Refactor) get 2 correction passes, prose agents (Reviewer, Explainer) get 1.

### Skills

Five declarative skills in `assist/skills/`:

- `project_rules` — Base style and quality rules with deterministic scoring rubric
- `code_review` — Output format for reviews
- `python_generation` — Type hint, docstring, naming conventions
- `refactor` — Refactoring patterns and behavioral-invariance protocol
- `documentation` — Structure for explanations

Each skill has a YAML frontmatter (v2.0) declaring `applies_to`, `priority`, `max_output_words`, `conflict_resolution`, `inject_position`, `self_check_persona`. Skills aren't generic suggestions to the model — they're contracts with explicit conflict-resolution rules and adversarial self-check personas.

### Task-aware verifier

`GlobalVerifier` runs three universal checks (syntax, non-empty, placeholders) but adapts to the task type. For `refactor`, output is markdown with an embedded code block — the verifier extracts the fenced `python` block before running `ast.parse` on it.

---

## Project layout

```
assist-cli/
├── assist/
│   ├── cli/                  # Typer commands and entry point
│   ├── core/                 # Orchestrator, registry, verifier, analyzers, builders
│   ├── agents/               # ReviewerAgent, GeneratorAgent, RefactorAgent, ExplainerAgent
│   ├── llm/                  # LLM client factory and adapters
│   ├── schemas/              # Pydantic models (TaskInput, AgentOutput, ...)
│   ├── skills/               # Declarative skills (.md with YAML frontmatter)
│   └── utils/                # File I/O and helpers
├── config/
│   └── registry.yaml         # Command → agent + skills mapping
├── tests/                    # 50 tests: integration, unit/agents, unit/core, unit/utils
├── pyproject.toml
└── README.md
```

---

## Testing

```bash
pytest
```

The 50 tests cover:

- **Integration tests** (3) — end-to-end pipelines (review, generate, refactor) with a `SequencedMockLLM` that simulates the self-validation loop deterministically
- **Agent unit tests** (6) — three tests per agent for `generate_draft`, `self_check`, `correct` in isolation
- **Core unit tests** (28+) — one per analyzer, plus verifier, prompt_builder, prompt_context_builder, registry, skill_resolver
- **Utility tests** (10+) — file readers, schemas, mock LLM client
- **CLI smoke test** (1)

All tests run without API calls thanks to mock LLM clients. Total runtime is under 5 seconds.

To run with coverage:

```bash
pytest --cov=assist
```

---

## Tech stack

- **Python 3.10+**
- **Typer** — CLI framework
- **Pydantic v2** — typed data contracts between modules
- **Rich** — terminal rendering (panels, tables, syntax highlighting)
- **PyYAML** — registry and skill frontmatter parsing
- **Anthropic SDK** — LLM client (Claude)
- **pytest** — testing framework

---

## Known limitations

Honest about what the system does not do well right now:

- **Large projects (500+ files)** — every invocation re-runs all analyzers; caching is not yet implemented
- **Python only** — analyzers are Python-specific, though the skill machinery is language-agnostic
- **Single LLM provider** — currently only Anthropic; the LLMFactory is designed to be extended
- **Files containing backticks** — refactoring files that contain triple-backtick sequences in their content (e.g. regex patterns) can break the markdown delimiter of the model's output. Documented edge case.
- **No execution caching** — two consecutive reviews of the same file redo everything, including LLM calls

None of these are blockers for typical use on medium-sized projects.

---

## Status

This is a personal project, version `0.1.0`. The four-agent pipeline is complete, the test suite is green, and the system has been validated end-to-end on its own codebase.

See `Assist_CLI_v3.docx` for the full project document (Italian) describing architecture, design decisions, and rationale in detail.

---

## License

MIT — see `LICENSE` for details.

## Author

Emanuele Pio De Bernardis
