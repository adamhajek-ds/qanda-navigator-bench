# qanda-navigator-bench

Benchmark how efficiently AI coding agents navigate codebases and answer developer questions.

The key metric is **AI Navigability Score** — total input tokens an agent consumes to correctly answer a question about a repository. Lower is better: an agent that finds the answer with less context is navigating more efficiently.

## How it works

1. You write a `qanda.yaml` in any repo with questions about that codebase
2. `qanda run` sends each question to a real AI coding agent (Claude Code, OpenCode)
3. A judge (LLM) compares the agent's answer to your golden answer using your acceptance criteria
4. You get a summary table with token usage, cost, accuracy, and timing
5. Results are auto-saved to `results/` with timestamps for tracking over time

## Prerequisites

- **Python 3.10+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** CLI (`claude`) — required for the default agent and for judging
- **[OpenCode](https://opencode.ai)** CLI (`opencode`) — only if using `--agent opencode`

## Installation

```bash
git clone https://github.com/adamhajek-ds/qanda-navigator-bench.git
cd qanda-navigator-bench
pip install -e .
```

## Quick start

### 1. Create a question file

In the repository you want to benchmark, create a `qanda.yaml`:

```yaml
questions:
  - id: auth-schema
    question: "What authorization model does the backend use and where is the schema defined?"
    golden_answer: |
      The backend uses OpenFGA. The schema is defined in
      src/services/authorization/openfga_authorization_schema.fga.
    acceptance_instructions: |
      Must identify OpenFGA and provide the correct schema file path.
    tags: [architecture, auth]

  - id: stt-metrics
    question: "What metrics do we use for STT evaluation?"
    golden_answer: |
      WER, CER, Normalized WER, Normalized CER, component latency,
      perceived latency, GPU utilization, RTF, token throughput,
      concurrent streams per GPU.
    acceptance_instructions: |
      Must list ALL metrics with no extras. This tests repo knowledge,
      not general knowledge.
    tags: [evaluation, stt]
```

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique identifier, used for filtering and result tracking |
| `question` | yes | The question sent to the agent |
| `golden_answer` | yes | Expected answer for the judge to compare against |
| `acceptance_instructions` | no | Custom criteria for the judge (e.g., "must list all items exactly") |
| `tags` | no | Labels for filtering (`--tags`) and grouped stats |

### 2. Run the benchmark

```bash
cd my-repo/

# Run all questions (looks for ./qanda.yaml by default)
qanda run

# Filter by tags
qanda run --tags architecture

# Run specific questions by ID
qanda run --questions auth-schema,stt-metrics

# Skip the judge (just measure token usage)
qanda run --no-judge

# Use a different model
qanda run --model sonnet

# Limit agent exploration depth
qanda run --max-turns 10

# Use OpenCode instead of Claude Code
qanda run --agent opencode
```

### 3. Read the results

Terminal output:

```
                            QnA Navigator Bench
┏━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━┓
┃ ID          ┃  OK?   ┃  Read ┃ Total In ┃  Out ┃ Turns ┃Models ┃  Cost ┃ Time ┃
┡━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━┩
│ auth-schema │ ✓ 0.95 │ 26.6k │    62.2k │  721 │     4 │opus   │ $0.20 │  21s │
│ stt-metrics │ ✗ 0.30 │ 85.1k │   180.4k │ 1.5k │     8 │opus   │ $0.45 │  52s │
├─────────────┼────────┼───────┼──────────┼──────┼───────┼───────┼───────┼──────┤
│ TOTAL       │  1/2   │111.7k │   242.6k │ 2.2k │    ~6 │       │ $0.65 │  73s │
└─────────────┴────────┴───────┴──────────┴──────┴───────┴───────┴───────┴──────┘

                          By Tag
┏━━━━━━━━━━━━━━┳━━━━┳━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Tag          ┃ Qs ┃ OK ┃ Avg Read ┃ Avg Total ┃ Avg Turns ┃ Avg Cost ┃ Avg Time ┃
┡━━━━━━━━━━━━━━╇━━━━╇━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ architecture │  1 │ 1/1│    26.6k │     62.2k │       4.0 │    $0.20 │      21s │
│ evaluation   │  1 │ 0/1│    85.1k │    180.4k │       8.0 │    $0.45 │      52s │
└──────────────┴────┴────┴──────────┴───────────┴───────────┴──────────┴──────────┘
```

**Key columns:**
- **Read** — new content the agent actually consumed (files, system prompt, tool results)
- **Total In** — all input tokens including re-sent conversation history across turns
- **Turns** — exploration steps the agent took
- **Models** — which models did the work (Claude Code may use sonnet + opus)

Judge details with per-question explanations are printed below the tables.

### 4. Track over time

Every run auto-saves a timestamped JSON to `results/` in this repo:

```
results/
├── 20260520-143512.json
├── 20260520-161023.json
└── 20260521-091445.json
```

Compare runs to measure the impact of documentation improvements, code restructuring, or CLAUDE.md changes on agent navigability.

## What this measures

The benchmark captures how **discoverable** and **readable** your codebase is for AI agents:

- High **Read** tokens = agent had to consume lots of content to find the answer (poor discoverability)
- Many **Turns** = agent explored widely before finding the right files (poor indexing/structure)
- Low **correctness** = information is ambiguous, scattered, or missing

Improving documentation structure, adding metadata, better file organization, or adding an `llms.txt` should measurably reduce these numbers.

## Project structure

```
src/qnb/
├── cli.py              # CLI entry point (argparse)
├── runner.py           # Question loading, filtering, benchmark loop
├── judge.py            # LLM-as-judge correctness evaluation
├── report.py           # Rich table output and JSON export
└── agents/
    ├── base.py         # Agent ABC, Question/AgentResult/ModelUsage dataclasses
    ├── claude_code.py  # Shells out to `claude -p --output-format json`
    └── opencode.py     # Shells out to `opencode run --format json`
```
