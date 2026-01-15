# API Design Specification

## Overview
This document specifies how to integrate with external LLM and Embedding APIs to power the SSR Market Research Tool.

## API Requirements

### LLM API (For Free-Text Responses)
- Generate natural language opinions about products
- Support system prompts (for persona enforcement)
- Cost-effective (prefer mini/small models)
- Streaming optional (for UI responsiveness)

### Embedding API (For Vectorization)
- Convert text to dense vectors (1536-dim preferred)
- Batch processing support
- Deterministic (same input → same output)
- Low latency (<100ms per request)

---

## Provider Selection

### Primary: OpenAI

#### LLM: GPT-5.2
**Why**:
- Best general-purpose model with improved intelligence
- Excellent instruction following and accuracy
- Configurable reasoning effort (none/low/medium/high/xhigh)
- Supports Responses API with chain-of-thought passing
- Better tool calling and context management

**Endpoint**: `https://api.openai.com/v1/responses` (Responses API)

**Fallback**: `gpt-5-mini` (cost-optimized) or `gpt-5-nano` (high-throughput)

---

#### Embeddings: text-embedding-3-small
**Why**:
- Industry standard (1536 dimensions)
- Cost-effective ($0.02 per 1M tokens)
- High quality for semantic similarity tasks
- Supports batch processing (up to 100 texts per request)

**Endpoint**: `https://api.openai.com/v1/embeddings`

**Fallback**: Local `sentence-transformers/all-MiniLM-L6-v2` (384-dim)

---

### Alternative: Anthropic

#### LLM: Claude 3.5 Haiku
**Why**:
- Comparable to GPT-4o-mini in quality
- Faster inference in some cases
- Alternative vendor (reduce single-point dependency)

**Endpoint**: `https://api.anthropic.com/v1/messages`

**Note**: Anthropic doesn't provide embeddings → must use OpenAI or local model

---

## LLM Integration Specification

### Request Format (OpenAI GPT-5.2)

```python
from openai import OpenAI

client = OpenAI()

def get_purchase_opinion(
    persona_system_prompt: str,
    product_description: str,
    model: str = "gpt-5.2",
    reasoning_effort: str = "none",
    verbosity: str = "medium",
    max_output_tokens: int = 200
) -> dict:
    """
    Get free-text purchase opinion from LLM using Responses API.

    Args:
        persona_system_prompt: System prompt enforcing persona identity
        product_description: Product concept to evaluate
        model: OpenAI model name (gpt-5.2, gpt-5-mini, gpt-5-nano)
        reasoning_effort: "none" (fast), "low", "medium", "high", "xhigh"
        verbosity: "low", "medium", "high" (controls output length)
        max_output_tokens: Limit response length

    Returns:
        {
            "response_text": str,
            "tokens_used": int,
            "cost": float,
            "latency_ms": int
        }
    """
    import time

    start_time = time.time()

    # Construct input combining system prompt and user query
    full_input = f"""{persona_system_prompt}

Here is a product concept:

"{product_description}"

Based on this description, explain your thoughts on whether you would purchase
this product. Focus on your reasoning and feelings about it.

IMPORTANT: Do NOT provide a numerical rating or score. Just explain your opinion
naturally, as you would to a friend."""

    # Make API call using Responses API
    response = client.responses.create(
        model=model,
        input=full_input,
        reasoning={
            "effort": reasoning_effort  # "none" for fast responses
        },
        text={
            "verbosity": verbosity  # "medium" for balanced output
        },
        max_output_tokens=max_output_tokens
    )

    # Extract data from Responses API format
    response_text = response.text.content.strip()
    tokens_used = response.usage.total_tokens

    # Calculate cost (pricing updated for GPT-5.2)
    cost = calculate_cost_openai(model, response.usage)

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "response_text": response_text,
        "tokens_used": tokens_used,
        "cost": cost,
        "latency_ms": latency_ms,
        "reasoning_tokens": getattr(response.usage, 'reasoning_tokens', 0)
    }
```

---

### Pricing Calculation

```python
# OpenAI pricing (as of 2025, GPT-5 family)
# Note: Exact pricing TBD - check https://openai.com/pricing
PRICING = {
    "gpt-5.2": {
        "input": 3.00 / 1_000_000,   # Estimated ~$3 per 1M input tokens
        "output": 15.00 / 1_000_000,  # Estimated ~$15 per 1M output tokens
        "reasoning": 15.00 / 1_000_000,  # Reasoning tokens (when effort > none)
    },
    "gpt-5-mini": {
        "input": 0.40 / 1_000_000,   # Cost-optimized
        "output": 1.60 / 1_000_000,
    },
    "gpt-5-nano": {
        "input": 0.10 / 1_000_000,   # High-throughput tasks
        "output": 0.40 / 1_000_000,
    },
    "text-embedding-3-small": {
        "usage": 0.02 / 1_000_000,  # $0.02 per 1M tokens
    }
}

def calculate_cost_openai(model: str, usage: dict) -> float:
    """
    Calculate cost of an OpenAI API call (GPT-5.2 Responses API).

    Args:
        model: Model name (e.g., "gpt-5.2", "gpt-5-mini")
        usage: Response usage object with:
            - input_tokens (replaces prompt_tokens)
            - output_tokens (replaces completion_tokens)
            - reasoning_tokens (for reasoning effort > none)

    Returns:
        Cost in USD (float)
    """
    if model not in PRICING:
        return 0.0  # Unknown model

    pricing = PRICING[model]

    if "input" in pricing:  # Chat/Reasoning model
        input_tokens = getattr(usage, 'input_tokens', 0)
        output_tokens = getattr(usage, 'output_tokens', 0)
        reasoning_tokens = getattr(usage, 'reasoning_tokens', 0)

        cost = (
            input_tokens * pricing["input"] +
            output_tokens * pricing["output"] +
            reasoning_tokens * pricing.get("reasoning", pricing["output"])
        )
    else:  # Embedding model
        cost = usage.total_tokens * pricing["usage"]

    return cost
```

---

### Response Validation

Ensure LLM response is valid for SSR:

```python
import re

def validate_llm_response(response_text: str) -> Tuple[bool, str]:
    """
    Validate that LLM response is suitable for SSR.

    Invalid responses:
    - Contains explicit numeric ratings ("4/5", "7 out of 10")
    - Too short (<10 characters)
    - Empty
    - Breaks character ("As an AI...")

    Returns:
        (is_valid, error_message)
    """
    # Check for empty
    if not response_text or len(response_text.strip()) < 10:
        return False, "Response too short or empty"

    # Check for numeric ratings
    numeric_patterns = [
        r'\d+\s*out of\s*\d+',     # "4 out of 5"
        r'\d+/\d+',                 # "4/5"
        r'rating:?\s*\d+',          # "rating: 4"
        r'score:?\s*\d+',           # "score: 7"
        r'\d+\s*stars?',            # "4 stars"
    ]

    for pattern in numeric_patterns:
        if re.search(pattern, response_text, re.IGNORECASE):
            return False, f"Response contains numeric rating: {pattern}"

    # Check for AI self-reference
    ai_phrases = ["as an ai", "i am an ai", "i'm an ai", "language model"]
    for phrase in ai_phrases:
        if phrase in response_text.lower():
            return False, "Response breaks character (AI self-reference)"

    return True, ""
```

---

### Retry Logic

```python
import time
from typing import Optional

def get_purchase_opinion_with_retry(
    persona_system_prompt: str,
    product_description: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Optional[dict]:
    """
    Get purchase opinion with exponential backoff retry.

    Args:
        persona_system_prompt: System prompt
        product_description: Product concept
        max_retries: Maximum retry attempts
        backoff_factor: Backoff multiplier (e.g., 2.0 = 1s, 2s, 4s)

    Returns:
        Response dict or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            response = get_purchase_opinion(
                persona_system_prompt,
                product_description
            )

            # Validate response
            is_valid, error_msg = validate_llm_response(response["response_text"])

            if is_valid:
                return response
            else:
                print(f"Invalid response (attempt {attempt + 1}): {error_msg}")
                # If invalid due to numeric rating, strengthen prompt
                if "numeric rating" in error_msg and attempt < max_retries - 1:
                    # Add stronger anti-numeric instruction
                    persona_system_prompt += "\n\nREMINDER: Never use numbers or ratings in your responses."
                    continue

        except openai.error.RateLimitError:
            wait_time = backoff_factor ** attempt
            print(f"Rate limit hit. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

        except openai.error.APIError as e:
            print(f"API error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(backoff_factor ** attempt)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    return None  # All retries exhausted
```

---

## Embedding Integration Specification

### Request Format (OpenAI)

```python
def get_embedding(
    text: str,
    model: str = "text-embedding-3-small"
) -> np.ndarray:
    """
    Get embedding vector for a single text.

    Args:
        text: Input text to embed
        model: OpenAI embedding model

    Returns:
        NumPy array of shape (1536,)
    """
    import openai

    response = openai.Embedding.create(
        input=text,
        model=model
    )

    embedding = np.array(response.data[0].embedding)

    return embedding
```

---

### Batch Embedding (Critical for Performance)

```python
def get_embeddings_batch(
    texts: List[str],
    model: str = "text-embedding-3-small",
    batch_size: int = 100
) -> np.ndarray:
    """
    Get embeddings for multiple texts (batched for efficiency).

    OpenAI allows up to 100 inputs per request.

    Args:
        texts: List of texts to embed
        model: Embedding model
        batch_size: Max texts per API call (OpenAI limit: 100)

    Returns:
        NumPy array of shape (N, 1536) where N = len(texts)
    """
    import openai

    all_embeddings = []

    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = openai.Embedding.create(
            input=batch,
            model=model
        )

        # Extract embeddings in order
        batch_embeddings = [
            item.embedding for item in sorted(response.data, key=lambda x: x.index)
        ]

        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings)
```

**Performance**:
- Single request: ~50ms per embedding
- Batch request (100 texts): ~500ms total → **5ms per embedding** (10x faster)

---

### Caching Strategy

Anchor embeddings never change → compute once, cache forever:

```python
import pickle
from pathlib import Path

CACHE_DIR = Path(".cache/embeddings")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_embedding_cached(text: str, model: str = "text-embedding-3-small") -> np.ndarray:
    """
    Get embedding with file-based caching.

    Cache key is hash of (text, model).
    """
    import hashlib

    # Generate cache key
    cache_key = hashlib.sha256(f"{text}|{model}".encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.pkl"

    # Check cache
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    # Compute embedding
    embedding = get_embedding(text, model)

    # Save to cache
    with open(cache_file, "wb") as f:
        pickle.dump(embedding, f)

    return embedding
```

**Usage**:
```python
# First call: API request (~50ms)
pos_vec = get_embedding_cached("I would definitely buy this product.")

# Subsequent calls: Disk read (<1ms)
pos_vec = get_embedding_cached("I would definitely buy this product.")
```

---

## Local Embedding Fallback (Optional)

For offline testing or cost optimization:

```python
from sentence_transformers import SentenceTransformer

# Load model once (cache to disk)
_local_model = None

def get_embedding_local(text: str) -> np.ndarray:
    """
    Get embedding using local model (no API call).

    Model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)

    Pros:
    - Free
    - Fast (~10ms on CPU)
    - Works offline

    Cons:
    - Lower quality than OpenAI
    - Different dimensionality (384 vs 1536)
    """
    global _local_model

    if _local_model is None:
        _local_model = SentenceTransformer('all-MiniLM-L6-v2')

    embedding = _local_model.encode(text, convert_to_numpy=True)

    return embedding  # Shape: (384,)
```

**Important**: If using local embeddings, ALL texts (responses + anchors) must use the same model.

---

## Rate Limiting

### OpenAI Limits (Tier 1)

| Model | Requests/min | Tokens/min |
|-------|-------------|------------|
| GPT-4o-mini | 500 | 200,000 |
| text-embedding-3-small | 3,000 | 1,000,000 |

### Implementation

```python
from ratelimit import limits, sleep_and_retry

# 500 requests per minute = ~8 per second
@sleep_and_retry
@limits(calls=8, period=1)
def rate_limited_completion(**kwargs):
    """Rate-limited wrapper for OpenAI completion."""
    return openai.ChatCompletion.create(**kwargs)
```

**For 100 respondents**:
- Sequential: ~100 seconds (1 per second to be safe)
- Parallel (8 workers): ~13 seconds

---

## Error Handling Matrix

| Error Type | HTTP Code | Action |
|------------|-----------|--------|
| Rate Limit | 429 | Retry with exponential backoff |
| Invalid API Key | 401 | Fail fast, show user error |
| Model Not Found | 404 | Switch to fallback model |
| Timeout | 504 | Retry up to 3 times |
| Server Error | 500/503 | Retry with backoff |
| Invalid Request | 400 | Log and skip (bad input) |

---

## Cost Tracking

```python
class CostTracker:
    """Track API costs across a survey session."""

    def __init__(self):
        self.total_cost = 0.0
        self.calls = []

    def record_call(self, model: str, usage: dict, cost: float):
        """Record an API call."""
        self.total_cost += cost
        self.calls.append({
            "model": model,
            "usage": usage,
            "cost": cost,
            "timestamp": time.time()
        })

    def summary(self) -> dict:
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "total_calls": len(self.calls),
            "avg_cost_per_call": self.total_cost / max(len(self.calls), 1),
            "breakdown": self._breakdown_by_model()
        }

    def _breakdown_by_model(self) -> dict:
        """Cost breakdown by model."""
        breakdown = {}
        for call in self.calls:
            model = call["model"]
            if model not in breakdown:
                breakdown[model] = {"calls": 0, "cost": 0.0}
            breakdown[model]["calls"] += 1
            breakdown[model]["cost"] += call["cost"]
        return breakdown
```

**Usage**:
```python
tracker = CostTracker()

for persona in personas:
    response = get_purchase_opinion(...)
    tracker.record_call("gpt-4o-mini", response["usage"], response["cost"])

print(tracker.summary())
# {
#   "total_cost": 0.52,
#   "total_calls": 100,
#   "avg_cost_per_call": 0.0052,
#   "breakdown": {"gpt-4o-mini": {"calls": 100, "cost": 0.52}}
# }
```

---

## Configuration Management

Store API keys and model preferences in `.env`:

```bash
# .env file (DO NOT COMMIT)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model preferences
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Behavior settings
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=200
ENABLE_CACHING=true
```

Load with `python-dotenv`:
```python
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
```

---

## Testing Strategy

### Unit Tests (Mocked)
```python
import pytest
from unittest.mock import patch, MagicMock

def test_get_purchase_opinion_success():
    """Test successful LLM response."""
    with patch("openai.ChatCompletion.create") as mock_create:
        # Mock response
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="I like this product."))],
            usage=MagicMock(total_tokens=50, prompt_tokens=30, completion_tokens=20)
        )

        result = get_purchase_opinion("system prompt", "product desc")

        assert result["response_text"] == "I like this product."
        assert result["tokens_used"] == 50
```

### Integration Tests (Live API)
```python
@pytest.mark.integration
def test_embedding_api_live():
    """Test real embedding API call."""
    text = "This is a test sentence."
    embedding = get_embedding(text)

    assert embedding.shape == (1536,)
    assert not np.isnan(embedding).any()
```

---

## Performance Benchmarks (Expected)

| Operation | Latency | Cost per 100 |
|-----------|---------|-------------|
| LLM response (gpt-4o-mini) | ~500ms | ~$0.50 |
| Embedding (single) | ~50ms | ~$0.0002 |
| Embedding (batch 100) | ~500ms | ~$0.02 |
| SSR calculation | <1ms | Free |

**Total for N=100**: ~1 minute, ~$0.52

---

**Next Steps**: Start implementation with [@fix_plan.md](../fix_plan.md).
