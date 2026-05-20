from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Question:
    id: str
    question: str
    golden_answer: str
    tags: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    question_id: str
    answer: str
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    total_cost_usd: float
    num_turns: int
    duration_ms: int
    raw_output: dict


class Agent(abc.ABC):
    name: str

    @abc.abstractmethod
    def run(self, question: str, working_dir: Path) -> AgentResult:
        ...
