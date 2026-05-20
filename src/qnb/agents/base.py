from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Question:
    id: str
    question: str
    golden_answer: str
    acceptance_instructions: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class ModelUsage:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float

    @property
    def total_input_tokens(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_creation_tokens


@dataclass
class AgentResult:
    question_id: str
    answer: str
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    num_turns: int
    duration_ms: int
    model_usage: list[ModelUsage]
    raw_output: dict

    @property
    def new_content_tokens(self) -> int:
        """Tokens the agent actually read (cache_creation + fresh input), excluding re-sent history."""
        return sum(m.input_tokens + m.cache_creation_tokens for m in self.model_usage)

    @property
    def resent_tokens(self) -> int:
        """Tokens re-sent from previous turns (cache_read)."""
        return sum(m.cache_read_tokens for m in self.model_usage)


class Agent(abc.ABC):
    name: str

    @abc.abstractmethod
    def run(self, question: str, working_dir: Path) -> AgentResult:
        ...
