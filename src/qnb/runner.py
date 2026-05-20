from __future__ import annotations

from pathlib import Path

import yaml

from .agents.base import Agent, AgentResult, Question


def load_questions(qanda_path: Path) -> list[Question]:
    with open(qanda_path) as f:
        data = yaml.safe_load(f)

    return [
        Question(
            id=q["id"],
            question=q["question"],
            golden_answer=q.get("golden_answer", ""),
            tags=q.get("tags", []),
        )
        for q in data["questions"]
    ]


def run_benchmark(
    agent: Agent,
    questions: list[Question],
    working_dir: Path,
    question_ids: list[str] | None = None,
) -> list[AgentResult]:
    if question_ids:
        questions = [q for q in questions if q.id in question_ids]

    results: list[AgentResult] = []
    for question in questions:
        result = agent.run(question.question, working_dir)
        result.question_id = question.id
        results.append(result)

    return results
