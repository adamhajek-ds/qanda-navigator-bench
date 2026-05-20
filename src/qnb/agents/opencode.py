from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .base import Agent, AgentResult, ModelUsage


class OpenCodeAgent(Agent):
    name = "opencode"

    def run(self, question: str, working_dir: Path) -> AgentResult:
        cmd = [
            "opencode",
            "run", question,
            "--format", "json",
        ]

        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"opencode exited with code {result.returncode}: {result.stderr}"
            )

        raw = json.loads(result.stdout)

        # opencode's JSON schema may differ — adapt as we discover the format
        usage = raw.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        model_usage = [ModelUsage(
            model=raw.get("model", "unknown"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=0,
            cache_creation_tokens=0,
            cost_usd=raw.get("total_cost_usd", 0.0),
        )]

        return AgentResult(
            question_id="",
            answer=raw.get("result", raw.get("output", "")),
            total_input_tokens=input_tokens,
            total_output_tokens=output_tokens,
            total_cost_usd=raw.get("total_cost_usd", 0.0),
            num_turns=raw.get("num_turns", 0),
            duration_ms=raw.get("duration_ms", 0),
            model_usage=model_usage,
            raw_output=raw,
        )
