# Assist CLI

Assist CLI is a modular command-line coding assistant for software development.

It is designed to generate, review, refactor, and explain code through a clean architecture built around:

- a central orchestrator
- declarative routing through a registry
- filesystem-based skills
- lightweight specialized agents
- a self-validation loop per agent
- a global verification layer
- deterministic testing with a mock LLM client

## Core Commands

- `assist generate <file|spec>`
- `assist review <file>`
- `assist refactor <file>`
- `assist explain <file>`

Optional advanced command:

- `assist ask <free_text>`

## Main Goals

Assist CLI is not a generic chat interface.  
It is a developer tool focused on:

- code quality
- maintainability
- clarity
- repeatable results
- testability
- clean architecture

## Architecture Overview

The system follows this flow:

CLI → Orchestrator → Registry → Skill Resolver → Agent → Self-Validation Loop → Global Verification Layer → Response Assembler → Output

## Key Design Choices

- **Registry-driven routing**: task-to-agent mapping is defined in YAML
- **Skills as modular files**: operational knowledge is stored in `SKILL.md` files
- **Typed interfaces**: cross-module data is handled with Pydantic models
- **Mockable LLM layer**: tests do not depend on real API calls
- **Limited self-check loop**: each agent can correct itself up to a configured maximum
- **Final verification step**: the output is checked before being returned

## Tech Stack

- Python 3.10+
- Typer
- Pydantic v2
- PyYAML
- pytest
- ruff
- mypy

## Project Structure

```text
assist-cli/
├── assist/
│   ├── cli/
│   ├── core/
│   ├── agents/
│   ├── llm/
│   ├── schemas/
│   ├── skills/
│   └── utils/
├── config/
├── docs/
├── tests/
├── CLAUDE.md
├── pyproject.toml
├── README.md
└── LICENSE