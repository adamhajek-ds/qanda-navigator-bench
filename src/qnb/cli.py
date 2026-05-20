from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from .agents.base import Agent
from .agents.claude_code import ClaudeCodeAgent
from .agents.opencode import OpenCodeAgent
from .judge import judge_answer
from .report import QuestionReport, export_json, print_summary
from .runner import load_questions, run_benchmark

AGENTS: dict[str, type[Agent]] = {
    "claude": ClaudeCodeAgent,
    "opencode": OpenCodeAgent,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="qnb",
        description="Benchmark AI coding agents on repo-specific Q&A",
    )
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run benchmark questions")
    run_parser.add_argument(
        "--qanda",
        type=Path,
        default=Path("qanda.yaml"),
        help="Path to qanda.yaml (default: ./qanda.yaml)",
    )
    run_parser.add_argument(
        "--agent",
        choices=list(AGENTS.keys()),
        default="claude",
    )
    run_parser.add_argument(
        "--model",
        help="Model override for the agent",
    )
    run_parser.add_argument(
        "--max-turns",
        type=int,
        help="Max agent turns per question",
    )
    run_parser.add_argument(
        "--questions",
        help="Comma-separated question IDs to run (default: all)",
    )
    run_parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip correctness judging",
    )
    run_parser.add_argument(
        "--judge-model",
        default="sonnet",
        help="Model for the judge (default: sonnet)",
    )
    run_parser.add_argument(
        "--output",
        type=Path,
        help="Export full results to JSON file",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    console = Console()

    if args.command != "run":
        console.print("[red]Usage: qnb run [OPTIONS][/]")
        sys.exit(1)

    if not args.qanda.exists():
        console.print(f"[red]File not found: {args.qanda}[/]")
        sys.exit(1)

    questions = load_questions(args.qanda)
    question_ids = args.questions.split(",") if args.questions else None
    working_dir = args.qanda.resolve().parent

    agent_cls = AGENTS[args.agent]
    agent_kwargs = {}
    if args.model and hasattr(agent_cls, "__init__"):
        agent_kwargs["model"] = args.model
    if args.max_turns and hasattr(agent_cls, "__init__"):
        agent_kwargs["max_turns"] = args.max_turns
    agent = agent_cls(**agent_kwargs)

    console.print(f"Running [bold]{len(questions)}[/] questions with [cyan]{agent.name}[/]...")
    console.print()

    results = run_benchmark(agent, questions, working_dir, question_ids)

    reports: list[QuestionReport] = []
    for result, question in zip(results, questions if not question_ids else [q for q in questions if q.id in question_ids]):
        verdict = None
        if not args.no_judge and question.golden_answer:
            console.print(f"  Judging {result.question_id}...")
            verdict = judge_answer(question.golden_answer, result.answer, model=args.judge_model)
        reports.append(QuestionReport(question_id=result.question_id, result=result, verdict=verdict))

    console.print()
    print_summary(reports, console)

    if args.output:
        export_json(reports, args.output)
        console.print(f"\nFull results exported to [cyan]{args.output}[/]")
