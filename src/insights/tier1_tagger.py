"""Tier1 response tagging using gpt-5-mini."""

import asyncio
import json
from dataclasses import dataclass
from typing import Optional

import openai

from ..llm_utils import get_max_tokens_param, normalize_reasoning_effort

TIER1_SYSTEM_PROMPT = """You are a precise data labeler for market research analysis.

For the given survey response, extract:
1. sentiment: Integer 1-10 (1=very negative, 10=very positive purchase intent)
2. category: ONE of [Price, UX, Trust, Feature, Convenience, Other]
3. keywords: Maximum 5 key words/phrases from the response

Output ONLY valid JSON, no explanation:
{"sentiment": 7, "category": "Price", "keywords": ["affordable", "value"]}"""


@dataclass
class Tier1TagResult:
    """Result from Tier1 tagging of a single response."""

    response_id: str
    sentiment: int  # 1-10
    category: str  # Price, UX, Trust, Feature, Convenience, Other
    keywords: list[str]
    original_text: str
    ssr_score: float


class Tier1Tagger:
    """Tier1 tagger using gpt-5-mini for response labeling."""

    def __init__(
        self,
        model: str = "gpt-5-mini",
        max_concurrent: int = 20,
    ):
        self.model = model
        self.max_concurrent = max_concurrent
        self.client = openai.AsyncOpenAI()
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def tag_single(
        self,
        response_id: str,
        response_text: str,
        ssr_score: float,
    ) -> Tier1TagResult:
        """Tag a single response with sentiment, category, and keywords."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        async with self._semaphore:
            try:
                reasoning_effort = normalize_reasoning_effort(self.model, "minimal")
                create_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": TIER1_SYSTEM_PROMPT},
                        {"role": "user", "content": response_text},
                    ],
                    **get_max_tokens_param(self.model, 150),
                }
                if reasoning_effort:
                    create_params["reasoning_effort"] = reasoning_effort

                completion = await self.client.chat.completions.create(**create_params)

                content = completion.choices[0].message.content or "{}"
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()

                data = json.loads(content)

                return Tier1TagResult(
                    response_id=response_id,
                    sentiment=int(data.get("sentiment", 5)),
                    category=data.get("category", "Other"),
                    keywords=data.get("keywords", [])[:5],
                    original_text=response_text,
                    ssr_score=ssr_score,
                )

            except (json.JSONDecodeError, KeyError, ValueError):
                # Fallback on parse error
                return Tier1TagResult(
                    response_id=response_id,
                    sentiment=5,
                    category="Other",
                    keywords=[],
                    original_text=response_text,
                    ssr_score=ssr_score,
                )

    async def tag_batch(
        self,
        responses: list[dict],
    ) -> list[Tier1TagResult]:
        """Tag multiple responses in parallel.

        Args:
            responses: List of dicts with keys: persona_id, response_text, ssr_score

        Returns:
            List of Tier1TagResult
        """
        tasks = [
            self.tag_single(
                response_id=r.get("persona_id", f"r_{i}"),
                response_text=r["response_text"],
                ssr_score=r.get("ssr_score", 0.5),
            )
            for i, r in enumerate(responses)
        ]
        return await asyncio.gather(*tasks)
