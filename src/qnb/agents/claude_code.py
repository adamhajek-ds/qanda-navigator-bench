from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .base import Agent, AgentResult, ModelUsage


def _parse_model_usage(raw: dict) -> list[ModelUsage]:
    entries = []
    for model, usage in raw.get("modelUsage", {}).items():
        entries.append(ModelUsage(
            model=model,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            cache_read_tokens=usage.get("cacheReadInputTokens", 0),
            cache_creation_tokens=usage.get("cacheCreationInputTokens", 0),
            cost_usd=usage.get("costUSD", 0.0),
        ))
    return entries


class ClaudeCodeAgent(Agent):
    name = "claude"

    def __init__(self, model: str | None = None, max_turns: int | None = None):
        self.model = model
        self.max_turns = max_turns

    def run(self, question: str, working_dir: Path) -> AgentResult:
        cmd = [
            "claude",
            "-p", question,
            "--output-format", "json",
        ]
        if self.model:
            cmd.extend(["--model", self.model])
        if self.max_turns:
            cmd.extend(["--max-turns", str(self.max_turns)])

        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"claude exited with code {result.returncode}: {result.stderr}"
            )

        raw = json.loads(result.stdout)
        model_usage = _parse_model_usage(raw)

        return AgentResult(
            question_id="",
            answer=raw.get("result", ""),
            total_input_tokens=sum(m.total_input_tokens for m in model_usage),
            total_output_tokens=sum(m.output_tokens for m in model_usage),
            total_cost_usd=raw.get("total_cost_usd", 0.0),
            num_turns=raw.get("num_turns", 0),
            duration_ms=raw.get("duration_ms", 0),
            model_usage=model_usage,
            raw_output=raw,
        )
