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
            acceptance_instructions=q.get("acceptance_instructions", ""),
            tags=q.get("tags", []),
        )
        for q in data["questions"]
    ]


def filter_questions(
    questions: list[Question],
    question_ids: list[str] | None = None,
    tags: set[str] | None = None,
) -> list[Question]:
    filtered = questions
    if question_ids:
        filtered = [q for q in filtered if q.id in question_ids]
    if tags:
        filtered = [q for q in filtered if tags & set(q.tags)]
    return filtered


def run_benchmark(
    agent: Agent,
    questions: list[Question],
    working_dir: Path,
    question_ids: list[str] | None = None,
    tags: set[str] | None = None,
) -> tuple[list[AgentResult], list[Question]]:
    filtered = filter_questions(questions, question_ids, tags)

    results: list[AgentResult] = []
    for question in filtered:
        result = agent.run(question.question, working_dir)
        result.question_id = question.id
        results.append(result)

    return results, filtered
