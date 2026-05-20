from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .agents.base import AgentResult, ModelUsage
from .judge import JudgeVerdict


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


@dataclass
class QuestionReport:
    question_id: str
    result: AgentResult
    verdict: JudgeVerdict | None


def _model_split(model_usage: list[ModelUsage]) -> str:
    total = sum(m.total_input_tokens for m in model_usage)
    if total == 0:
        return "—"
    parts = []
    for m in sorted(model_usage, key=lambda x: x.total_input_tokens, reverse=True):
        pct = m.total_input_tokens / total * 100
        short_name = m.model.split("-")[1] if "-" in m.model else m.model
        parts.append(f"{short_name} {pct:.0f}%")
    return " / ".join(parts)


def _cache_hit_rate(model_usage: list[ModelUsage]) -> str:
    total_in = sum(m.total_input_tokens for m in model_usage)
    cache_read = sum(m.cache_read_tokens for m in model_usage)
    if total_in == 0:
        return "—"
    return f"{cache_read / total_in * 100:.0f}%"


def print_summary(reports: list[QuestionReport], console: Console | None = None) -> None:
    console = console or Console()

    table = Table(title="QnA Navigator Bench", expand=False, padding=(0, 1))
    table.add_column("ID", style="cyan")
    table.add_column("OK?", justify="center")
    table.add_column("In Tok", justify="right")
    table.add_column("Out Tok", justify="right")
    table.add_column("Turns", justify="right")
    table.add_column("Tok/T", justify="right")
    table.add_column("Cache%", justify="right")
    table.add_column("Models")
    table.add_column("Cost", justify="right")
    table.add_column("Time", justify="right")

    totals = dict(in_tok=0, out_tok=0, turns=0, cost=0.0, duration=0, correct=0)

    for report in reports:
        r = report.result
        totals["in_tok"] += r.total_input_tokens
        totals["out_tok"] += r.total_output_tokens
        totals["turns"] += r.num_turns
        totals["cost"] += r.total_cost_usd
        totals["duration"] += r.duration_ms

        if report.verdict:
            v = report.verdict
            verdict_str = f"[green]✓[/] {v.confidence:.2f}" if v.correct else f"[red]✗[/] {v.confidence:.2f}"
            if v.correct:
                totals["correct"] += 1
        else:
            verdict_str = "—"

        tok_per_turn = r.total_input_tokens // r.num_turns if r.num_turns else 0

        table.add_row(
            r.question_id,
            verdict_str,
            _fmt_tokens(r.total_input_tokens),
            _fmt_tokens(r.total_output_tokens),
            str(r.num_turns),
            _fmt_tokens(tok_per_turn),
            _cache_hit_rate(r.model_usage),
            _model_split(r.model_usage),
            f"${r.total_cost_usd:.2f}",
            f"{r.duration_ms / 1000:.0f}s",
        )

    n = len(reports)
    avg_turns = totals["turns"] / n if n else 0
    avg_tok_per_turn = totals["in_tok"] // totals["turns"] if totals["turns"] else 0
    table.add_section()
    table.add_row(
        "TOTAL",
        f"{totals['correct']}/{n}" if any(r.verdict for r in reports) else "—",
        _fmt_tokens(totals["in_tok"]),
        _fmt_tokens(totals["out_tok"]),
        f"~{avg_turns:.0f}",
        _fmt_tokens(avg_tok_per_turn),
        "",
        "",
        f"${totals['cost']:.2f}",
        f"{totals['duration'] / 1000:.0f}s",
        style="bold",
    )

    console.print(table)

    has_verdicts = any(r.verdict for r in reports)
    if has_verdicts:
        console.print()
        console.print("[bold]Judge Details[/]")
        for report in reports:
            if not report.verdict:
                continue
            v = report.verdict
            icon = "[green]✓[/]" if v.correct else "[red]✗[/]"
            console.print(
                Panel(
                    v.explanation,
                    title=f"{icon} {report.question_id} — confidence {v.confidence:.2f}",
                    border_style="green" if v.correct else "red",
                    width=100,
                )
            )


def _result_to_dict(r: AgentResult) -> dict:
    d = asdict(r)
    del d["raw_output"]
    return d


def export_json(reports: list[QuestionReport], path: Path) -> None:
    results = []
    for r in reports:
        entry = {
            "question_id": r.question_id,
            "result": _result_to_dict(r.result),
            "verdict": asdict(r.verdict) if r.verdict else None,
            "derived": {
                "tokens_per_turn": r.result.total_input_tokens // r.result.num_turns if r.result.num_turns else 0,
                "cache_hit_rate": sum(m.cache_read_tokens for m in r.result.model_usage) / max(r.result.total_input_tokens, 1),
                "model_split": {
                    m.model: m.total_input_tokens / max(r.result.total_input_tokens, 1)
                    for m in r.result.model_usage
                },
            },
        }
        results.append(entry)

    n = len(reports)
    total_turns = sum(r.result.num_turns for r in reports)
    data = {
        "results": results,
        "summary": {
            "total_questions": n,
            "correct": sum(1 for r in reports if r.verdict and r.verdict.correct),
            "total_input_tokens": sum(r.result.total_input_tokens for r in reports),
            "total_output_tokens": sum(r.result.total_output_tokens for r in reports),
            "total_cost_usd": sum(r.result.total_cost_usd for r in reports),
            "avg_turns": total_turns / n if n else 0,
            "avg_tokens_per_turn": sum(r.result.total_input_tokens for r in reports) // max(total_turns, 1),
            "total_duration_ms": sum(r.result.duration_ms for r in reports),
        },
    }
    path.write_text(json.dumps(data, indent=2))
