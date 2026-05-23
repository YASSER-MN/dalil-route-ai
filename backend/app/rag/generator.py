from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from groq import Groq

from backend.app.rag.retriever import Chunk

_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_v1.txt"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

MODEL = "llama-3.3-70b-versatile"
PROMPT_VERSION = "v1"


@dataclass(frozen=True)
class Answer:
    text: str
    model: str
    prompt_version: str
    evidence_ids: list[str]


class AnswerGenerator:
    def __init__(self, api_key: str | None = None) -> None:
        self._client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))

    def generate(self, question: str, evidence: list[Chunk]) -> Answer:
        evidence_block = "\n".join(
            f'<evidence article="{chunk.article_number}">{chunk.text}</evidence>'
            for chunk in evidence
        )
        user_message = f"Question: {question}\n\nEvidence:\n{evidence_block}"

        response = self._client.chat.completions.create(
            model=MODEL,
            temperature=0.1,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        answer_text = response.choices[0].message.content or ""
        return Answer(
            text=answer_text,
            model=MODEL,
            prompt_version=PROMPT_VERSION,
            evidence_ids=[chunk.id for chunk in evidence],
        )
