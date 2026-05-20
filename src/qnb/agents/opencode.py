from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .base import Agent, AgentResult


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

        return AgentResult(
            question_id="",
            answer=raw.get("result", raw.get("output", "")),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            total_cost_usd=raw.get("total_cost_usd", 0.0),
            num_turns=raw.get("num_turns", 0),
            duration_ms=raw.get("duration_ms", 0),
            raw_output=raw,
        )
