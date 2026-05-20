# qanda-navigator-bench

Benchmarking tool that measures how efficiently AI coding agents (Claude Code, OpenCode) can navigate a codebase and answer developer questions.

## Key metric
**AI Navigability Score** — total input tokens an agent consumes to correctly answer a question about a repo.

## Tech stack
- Python 3.12+
- uv for dependency management
- CLI agents: `claude` (Claude Code), `opencode`

## Project structure
- `src/qnb/` — main package
- `questions/` — question dataset YAML files
- `results/` — benchmark outputs (gitignored)

## Conventions
- Use `uv` for all dependency management
- Keep it simple — this is a measurement tool, not a framework
