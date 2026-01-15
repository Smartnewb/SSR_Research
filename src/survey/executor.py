"""Survey execution module for LLM interactions."""

import time
from typing import Optional

from .prompts import create_survey_prompt, create_reinforced_prompt
from .validator import validate_llm_response


PRICING = {
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
    "gpt-5-mini": {
        "input": 0.40 / 1_000_000,
        "output": 1.60 / 1_000_000,
    },
    "gpt-5.2": {
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000,
        "reasoning": 15.00 / 1_000_000,
    },
    "gpt-5-nano": {
        "input": 0.10 / 1_000_000,
        "output": 0.40 / 1_000_000,
    },
}


def calculate_cost(model: str, usage: dict) -> float:
    """
    Calculate cost of an OpenAI API call.

    Args:
        model: Model name
        usage: Usage dict with prompt_tokens and completion_tokens

    Returns:
        Cost in USD
    """
    if model not in PRICING:
        return 0.0

    pricing = PRICING[model]

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    reasoning_tokens = usage.get("reasoning_tokens", 0)

    cost = (
        prompt_tokens * pricing["input"]
        + completion_tokens * pricing["output"]
        + reasoning_tokens * pricing.get("reasoning", pricing["output"])
    )

    return cost


def get_purchase_opinion(
    persona_system_prompt: str,
    product_description: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 200,
    temperature: float = 0.7,
    client: Optional["openai.OpenAI"] = None,
) -> dict:
    """
    Get free-text purchase opinion from LLM.

    Args:
        persona_system_prompt: System prompt enforcing persona identity
        product_description: Product concept to evaluate
        model: OpenAI model name
        max_tokens: Max response length
        temperature: Sampling temperature
        client: Optional OpenAI client

    Returns:
        {
            "response_text": str,
            "tokens_used": int,
            "cost": float,
            "latency_ms": int,
            "model": str,
        }
    """
    if client is None:
        import openai
        client = openai.OpenAI()

    start_time = time.time()

    user_prompt = create_survey_prompt(product_description)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": persona_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    response_text = response.choices[0].message.content.strip()

    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
    }

    cost = calculate_cost(model, usage)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "response_text": response_text,
        "tokens_used": response.usage.total_tokens,
        "cost": cost,
        "latency_ms": latency_ms,
        "model": model,
        "usage": usage,
    }


def get_purchase_opinion_with_retry(
    persona_system_prompt: str,
    product_description: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    model: str = "gpt-4o-mini",
    client: Optional["openai.OpenAI"] = None,
) -> Optional[dict]:
    """
    Get purchase opinion with exponential backoff retry.

    Retries on rate limits, API errors, and invalid responses.

    Args:
        persona_system_prompt: System prompt
        product_description: Product concept
        max_retries: Maximum retry attempts
        backoff_factor: Backoff multiplier
        model: Model name
        client: Optional OpenAI client

    Returns:
        Response dict or None if all retries failed
    """
    import openai

    reinforced = False

    for attempt in range(max_retries):
        try:
            if reinforced:
                user_prompt = create_reinforced_prompt(product_description)
            else:
                user_prompt = create_survey_prompt(product_description)

            if client is None:
                client = openai.OpenAI()

            start_time = time.time()

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": persona_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content.strip()

            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

            is_valid, error_msg = validate_llm_response(response_text)

            if is_valid:
                return {
                    "response_text": response_text,
                    "tokens_used": response.usage.total_tokens,
                    "cost": calculate_cost(model, usage),
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "model": model,
                    "usage": usage,
                    "attempts": attempt + 1,
                }
            else:
                if "numeric rating" in error_msg and attempt < max_retries - 1:
                    reinforced = True
                    continue

        except openai.RateLimitError:
            wait_time = backoff_factor ** attempt
            time.sleep(wait_time)

        except openai.APIError:
            if attempt == max_retries - 1:
                return None
            time.sleep(backoff_factor ** attempt)

        except Exception:
            return None

    return None


class CostTracker:
    """Track API costs across a survey session."""

    def __init__(self):
        """Initialize cost tracker."""
        self.total_cost = 0.0
        self.calls: list[dict] = []

    def record_call(self, model: str, usage: dict, cost: float) -> None:
        """Record an API call."""
        self.total_cost += cost
        self.calls.append({
            "model": model,
            "usage": usage,
            "cost": cost,
            "timestamp": time.time(),
        })

    def summary(self) -> dict:
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "total_calls": len(self.calls),
            "avg_cost_per_call": (
                self.total_cost / len(self.calls) if self.calls else 0.0
            ),
            "breakdown": self._breakdown_by_model(),
        }

    def _breakdown_by_model(self) -> dict:
        """Cost breakdown by model."""
        breakdown: dict[str, dict] = {}
        for call in self.calls:
            model = call["model"]
            if model not in breakdown:
                breakdown[model] = {"calls": 0, "cost": 0.0}
            breakdown[model]["calls"] += 1
            breakdown[model]["cost"] += call["cost"]
        return breakdown

    def reset(self) -> None:
        """Reset tracker."""
        self.total_cost = 0.0
        self.calls.clear()
