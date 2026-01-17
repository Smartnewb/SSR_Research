"""Survey execution module for LLM interactions."""

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from .prompts import create_survey_prompt, create_reinforced_prompt
from .validator import validate_llm_response

logger = logging.getLogger(__name__)


def _get_default_model() -> str:
    """Get default model from environment or fallback."""
    return os.getenv("SURVEY_MODEL", os.getenv("LLM_MODEL", "gpt-5-nano"))


def _get_reasoning_effort() -> str:
    """Get reasoning effort from environment or fallback."""
    return os.getenv("SURVEY_REASONING_EFFORT", "none")


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

GPT5_MODELS = {"gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5.2"}


def get_max_tokens_param(model: str, value: int) -> dict:
    """Return appropriate max tokens parameter based on model.

    GPT-5 series uses 'max_completion_tokens' instead of 'max_tokens'.
    """
    if model in GPT5_MODELS:
        return {"max_completion_tokens": value}
    return {"max_tokens": value}


def supports_temperature(model: str, reasoning_effort: str = "none") -> bool:
    """Check if model supports temperature parameter.

    Per GPT-5.2 docs: temperature, top_p, logprobs are ONLY supported
    when reasoning_effort is set to "none".

    Additionally, gpt-5-nano only supports the default temperature (1).

    Args:
        model: Model name
        reasoning_effort: Current reasoning effort setting

    Returns:
        True if temperature can be used with non-default values
    """
    # gpt-5-nano only supports default temperature (1)
    if model == "gpt-5-nano":
        return False
    if model not in GPT5_MODELS:
        return True
    return reasoning_effort == "none"


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
    model: Optional[str] = None,
    max_tokens: int = 200,
    temperature: float = 0.7,
    reasoning_effort: Optional[str] = None,
    client: Optional["openai.OpenAI"] = None,
) -> dict:
    """
    Get free-text purchase opinion from LLM.

    Args:
        persona_system_prompt: System prompt enforcing persona identity
        product_description: Product concept to evaluate
        model: OpenAI model name (default from env SURVEY_MODEL or LLM_MODEL)
        max_tokens: Max response length
        temperature: Sampling temperature (only used when reasoning_effort=none)
        reasoning_effort: Reasoning effort level (none/low/medium/high/xhigh)
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

    model = model or _get_default_model()
    reasoning_effort = reasoning_effort or _get_reasoning_effort()

    start_time = time.time()

    user_prompt = create_survey_prompt(product_description)

    api_params = {
        "model": model,
        "messages": [
            {"role": "system", "content": persona_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **get_max_tokens_param(model, max_tokens),
    }

    if supports_temperature(model, reasoning_effort):
        api_params["temperature"] = temperature

    response = client.chat.completions.create(**api_params)

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
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
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
        model: Model name (default from env)
        reasoning_effort: Reasoning effort level
        client: Optional OpenAI client

    Returns:
        Response dict or None if all retries failed
    """
    import openai

    model = model or _get_default_model()
    reasoning_effort = reasoning_effort or _get_reasoning_effort()
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

            # GPT-5 models need more tokens
            # gpt-5-nano needs 1000+ with minimal reasoning to produce actual text
            if model == "gpt-5-nano":
                max_tokens = 1000
            elif model in GPT5_MODELS:
                max_tokens = 800
            else:
                max_tokens = 200

            api_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": persona_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **get_max_tokens_param(model, max_tokens),
            }

            # Add reasoning_effort for GPT-5 models
            if model in GPT5_MODELS and reasoning_effort:
                api_params["reasoning_effort"] = reasoning_effort

            if supports_temperature(model, reasoning_effort):
                api_params["temperature"] = 0.7

            response = client.chat.completions.create(**api_params)

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

            if "numeric rating" in error_msg and attempt < max_retries - 1:
                reinforced = True
                continue

        except openai.RateLimitError as e:
            logger.warning(f"Rate limit hit on attempt {attempt + 1}/{max_retries}: {e}")
            wait_time = backoff_factor ** attempt
            time.sleep(wait_time)

        except openai.APIError as e:
            logger.error(f"OpenAI API error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed due to API error: {e}")
                return None
            time.sleep(backoff_factor ** attempt)

        except Exception as e:
            logger.error(f"Unexpected error during survey API call: {type(e).__name__}: {e}")
            return None

    logger.error(f"All {max_retries} attempts failed for survey API call")
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


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 500
    tokens_per_minute: int = 150_000
    requests_per_day: int = 10_000
    burst_multiplier: float = 1.5


class TokenBucketRateLimiter:
    """
    Token Bucket rate limiter for OpenAI API calls.

    Implements dual bucket limiting:
    - Request bucket: Limits requests per minute (RPM)
    - Token bucket: Limits tokens per minute (TPM)

    Prevents batch failures on large-scale surveys (1,000+ personas).
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._lock = threading.Lock()

        self.request_tokens = float(self.config.requests_per_minute)
        self.token_tokens = float(self.config.tokens_per_minute)

        self.request_capacity = self.config.requests_per_minute * self.config.burst_multiplier
        self.token_capacity = self.config.tokens_per_minute * self.config.burst_multiplier

        self.last_refill = time.time()

        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "waits": 0,
            "total_wait_time": 0.0,
        }

    def _refill(self) -> None:
        """Refill buckets based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now

        refill_per_second_requests = self.config.requests_per_minute / 60.0
        refill_per_second_tokens = self.config.tokens_per_minute / 60.0

        self.request_tokens = min(
            self.request_capacity,
            self.request_tokens + elapsed * refill_per_second_requests,
        )
        self.token_tokens = min(
            self.token_capacity,
            self.token_tokens + elapsed * refill_per_second_tokens,
        )

    def acquire(self, estimated_tokens: int = 1000) -> float:
        """
        Acquire permission to make an API call.

        Blocks until rate limit allows the request.

        Args:
            estimated_tokens: Estimated tokens for this request

        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        total_wait = 0.0

        with self._lock:
            self._refill()

            while self.request_tokens < 1 or self.token_tokens < estimated_tokens:
                self._refill()

                wait_for_request = 0.0
                wait_for_tokens = 0.0

                if self.request_tokens < 1:
                    needed = 1 - self.request_tokens
                    refill_rate = self.config.requests_per_minute / 60.0
                    wait_for_request = needed / refill_rate

                if self.token_tokens < estimated_tokens:
                    needed = estimated_tokens - self.token_tokens
                    refill_rate = self.config.tokens_per_minute / 60.0
                    wait_for_tokens = needed / refill_rate

                wait_time = max(wait_for_request, wait_for_tokens, 0.1)
                wait_time = min(wait_time, 60.0)

                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                total_wait += wait_time
                self.stats["waits"] += 1

                self._refill()

            self.request_tokens -= 1
            self.token_tokens -= estimated_tokens
            self.stats["total_requests"] += 1
            self.stats["total_tokens"] += estimated_tokens

        if total_wait > 0:
            self.stats["total_wait_time"] += total_wait
            logger.info(f"Rate limit: waited {total_wait:.2f}s total")

        return total_wait

    def report_actual_usage(self, actual_tokens: int, estimated_tokens: int) -> None:
        """
        Report actual token usage to adjust bucket.

        Args:
            actual_tokens: Actual tokens used
            estimated_tokens: Previously estimated tokens
        """
        diff = estimated_tokens - actual_tokens
        if diff != 0:
            with self._lock:
                self.token_tokens = min(
                    self.token_capacity,
                    self.token_tokens + diff,
                )
                self.stats["total_tokens"] += (actual_tokens - estimated_tokens)

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            **self.stats,
            "current_request_tokens": self.request_tokens,
            "current_token_tokens": self.token_tokens,
            "avg_wait_time": (
                self.stats["total_wait_time"] / self.stats["waits"]
                if self.stats["waits"] > 0 else 0.0
            ),
        }

    def reset(self) -> None:
        """Reset rate limiter to initial state."""
        with self._lock:
            self.request_tokens = float(self.config.requests_per_minute)
            self.token_tokens = float(self.config.tokens_per_minute)
            self.last_refill = time.time()
            self.stats = {
                "total_requests": 0,
                "total_tokens": 0,
                "waits": 0,
                "total_wait_time": 0.0,
            }


class AsyncTokenBucketRateLimiter:
    """Async version of Token Bucket rate limiter."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize async rate limiter."""
        self.config = config or RateLimitConfig()
        self._lock = asyncio.Lock()

        self.request_tokens = float(self.config.requests_per_minute)
        self.token_tokens = float(self.config.tokens_per_minute)

        self.request_capacity = self.config.requests_per_minute * self.config.burst_multiplier
        self.token_capacity = self.config.tokens_per_minute * self.config.burst_multiplier

        self.last_refill = time.time()

    def _refill(self) -> None:
        """Refill buckets based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now

        refill_per_second_requests = self.config.requests_per_minute / 60.0
        refill_per_second_tokens = self.config.tokens_per_minute / 60.0

        self.request_tokens = min(
            self.request_capacity,
            self.request_tokens + elapsed * refill_per_second_requests,
        )
        self.token_tokens = min(
            self.token_capacity,
            self.token_tokens + elapsed * refill_per_second_tokens,
        )

    async def acquire(self, estimated_tokens: int = 1000) -> float:
        """
        Acquire permission to make an API call (async).

        Args:
            estimated_tokens: Estimated tokens for this request

        Returns:
            Wait time in seconds
        """
        total_wait = 0.0

        async with self._lock:
            self._refill()

            while self.request_tokens < 1 or self.token_tokens < estimated_tokens:
                self._refill()

                wait_for_request = 0.0
                wait_for_tokens = 0.0

                if self.request_tokens < 1:
                    needed = 1 - self.request_tokens
                    refill_rate = self.config.requests_per_minute / 60.0
                    wait_for_request = needed / refill_rate

                if self.token_tokens < estimated_tokens:
                    needed = estimated_tokens - self.token_tokens
                    refill_rate = self.config.tokens_per_minute / 60.0
                    wait_for_tokens = needed / refill_rate

                wait_time = max(wait_for_request, wait_for_tokens, 0.1)
                wait_time = min(wait_time, 60.0)

                await asyncio.sleep(wait_time)
                total_wait += wait_time

                self._refill()

            self.request_tokens -= 1
            self.token_tokens -= estimated_tokens

        return total_wait
