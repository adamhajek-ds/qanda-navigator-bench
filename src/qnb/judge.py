from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass
class JudgeVerdict:
    correct: bool
    confidence: float
    explanation: str


JUDGE_PROMPT = """\
You are a judge evaluating whether an AI agent's answer is correct.

## Golden answer (expected)
{golden_answer}

## Agent's answer
{agent_answer}

Evaluate whether the agent's answer captures the key facts from the golden answer.
Minor wording differences are fine. The agent may include additional correct details.
What matters is whether the core information is present and accurate.

Respond with exactly this JSON (no other text):
{{"correct": true/false, "confidence": 0.0-1.0, "explanation": "brief reason"}}
"""


def judge_answer(
    golden_answer: str,
    agent_answer: str,
    model: str = "sonnet",
) -> JudgeVerdict:
    prompt = JUDGE_PROMPT.format(
        golden_answer=golden_answer,
        agent_answer=agent_answer,
    )

    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--model", model],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return JudgeVerdict(correct=False, confidence=0.0, explanation="Judge failed to run")

    raw = json.loads(result.stdout)
    answer_text = raw.get("result", "")

    try:
        verdict = json.loads(answer_text)
        return JudgeVerdict(
            correct=verdict["correct"],
            confidence=verdict["confidence"],
            explanation=verdict["explanation"],
        )
    except (json.JSONDecodeError, KeyError):
        return JudgeVerdict(
            correct=False,
            confidence=0.0,
            explanation=f"Could not parse judge output: {answer_text[:200]}",
        )
