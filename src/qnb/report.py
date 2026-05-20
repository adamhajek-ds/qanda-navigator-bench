from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .agents.base import AgentResult
from .judge import JudgeVerdict


@dataclass
class QuestionReport:
    question_id: str
    result: AgentResult
    verdict: JudgeVerdict | None


def print_summary(reports: list[QuestionReport], console: Console | None = None) -> None:
    console = console or Console()

    table = Table(title="QnA Navigator Bench Results")
    table.add_column("ID", style="cyan")
    table.add_column("Correct", justify="center")
    table.add_column("Input Tokens", justify="right")
    table.add_column("Turns", justify="right")
    table.add_column("Cost ($)", justify="right")
    table.add_column("Time", justify="right")

    total_tokens = 0
    total_turns = 0
    total_cost = 0.0
    total_duration = 0
    correct_count = 0

    for report in reports:
        r = report.result
        total_tokens += r.total_input_tokens
        total_turns += r.num_turns
        total_cost += r.total_cost_usd
        total_duration += r.duration_ms

        if report.verdict:
            v = report.verdict
            correct_str = f"[green]✓[/] ({v.confidence:.2f})" if v.correct else f"[red]✗[/] ({v.confidence:.2f})"
            if v.correct:
                correct_count += 1
        else:
            correct_str = "—"

        table.add_row(
            r.question_id,
            correct_str,
            f"{r.total_input_tokens:,}",
            str(r.num_turns),
            f"{r.total_cost_usd:.4f}",
            f"{r.duration_ms / 1000:.1f}s",
        )

    n = len(reports)
    avg_turns = total_turns / n if n else 0
    table.add_section()
    table.add_row(
        "TOTAL",
        f"{correct_count}/{n}" if any(r.verdict for r in reports) else "—",
        f"{total_tokens:,}",
        f"avg {avg_turns:.1f}",
        f"{total_cost:.4f}",
        f"{total_duration / 1000:.1f}s",
        style="bold",
    )

    console.print(table)


def _result_to_dict(r: AgentResult) -> dict:
    d = asdict(r)
    del d["raw_output"]
    return d


def export_json(reports: list[QuestionReport], path: Path) -> None:
    data = {
        "results": [
            {
                "question_id": r.question_id,
                "result": _result_to_dict(r.result),
                "verdict": asdict(r.verdict) if r.verdict else None,
            }
            for r in reports
        ],
        "summary": {
            "total_questions": len(reports),
            "correct": sum(1 for r in reports if r.verdict and r.verdict.correct),
            "total_input_tokens": sum(r.result.total_input_tokens for r in reports),
            "total_cost_usd": sum(r.result.total_cost_usd for r in reports),
            "avg_turns": sum(r.result.num_turns for r in reports) / len(reports) if reports else 0,
            "total_duration_ms": sum(r.result.duration_ms for r in reports),
        },
    }
    path.write_text(json.dumps(data, indent=2))
