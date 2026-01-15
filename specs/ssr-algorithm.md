# SSR Algorithm Specification

## Overview
The **Semantic Similarity Rating (SSR)** algorithm converts free-text opinions into numerical purchase intent scores by measuring the proximity of response embeddings to semantic anchors.

## Core Concept

Traditional approach (WRONG):
```
LLM: "Rate this product 1-5"
Response: "3" (central tendency bias)
```

SSR approach (CORRECT):
```
LLM: "Explain your opinion naturally"
Response: "It looks useful but too expensive for my budget..."
Embedding: [0.23, -0.45, 0.89, ...]  (1536-dim vector)
Similarity to "I would buy": 0.42
Similarity to "I wouldn't buy": 0.73
Final Score: 3.2 / 10  (derived from projection)
```

---

## Mathematical Foundation

### Step 1: Define Semantic Anchors

We use two anchor texts representing the extremes of the purchase intent scale:

```python
POSITIVE_ANCHOR = "I would definitely buy this product."
NEGATIVE_ANCHOR = "I would never buy this product."
```

**Why these specific texts?**
- Simple, unambiguous statements
- Clear directional intent
- Language matches natural responses
- Tested to maximize cosine distance (from paper)

**Embedding**:
```python
pos_vec = embed(POSITIVE_ANCHOR)  # Shape: (1536,)
neg_vec = embed(NEGATIVE_ANCHOR)  # Shape: (1536,)
```

---

### Step 2: Define the Semantic Axis

The "axis" is the vector connecting the negative anchor to the positive anchor:

```python
semantic_axis = pos_vec - neg_vec
```

This vector represents the direction of "increasing purchase intent" in embedding space.

**Geometric Interpretation**:
```
Embedding Space (simplified to 2D):

       pos_vec (Buy)
          ●
         /│
        / │
       /  │ semantic_axis
      /   │
     /    │
    /     ●───────── response_vec
   ●
 neg_vec (Don't Buy)
```

The SSR score is essentially: **How far along the axis is the response?**

---

### Step 3: Calculate Cosine Similarity

For a given response embedding `response_vec`, we calculate its similarity to the positive anchor:

```python
def cosine_similarity(vec_a, vec_b):
    """
    Compute cosine similarity between two vectors.

    cos(θ) = (A · B) / (||A|| × ||B||)

    Returns value in [-1, 1]:
    - 1.0 = identical direction
    - 0.0 = orthogonal
    - -1.0 = opposite direction
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)
```

**Alternative** (using scikit-learn):
```python
from sklearn.metrics.pairwise import cosine_similarity

sim_pos = cosine_similarity(
    response_vec.reshape(1, -1),
    pos_vec.reshape(1, -1)
)[0][0]
```

---

### Step 4: Compute SSR Score (Projection Method)

The paper uses a projection formula, but for the MVP we'll use a simplified approach:

#### Simplified SSR (MVP Implementation)

```python
def calculate_ssr_simple(response_vec, pos_vec, neg_vec):
    """
    Simplified SSR calculation.

    The score is derived from similarity to the positive anchor,
    normalized to [0, 1] range.

    Formula:
    score = (sim_pos + 1) / 2

    Where sim_pos is cosine similarity to positive anchor.
    Cosine ranges from [-1, 1], so this maps to [0, 1].
    """
    sim_pos = cosine_similarity(response_vec, pos_vec)

    # Normalize from [-1, 1] to [0, 1]
    score = (sim_pos + 1) / 2

    return score
```

**Output Range**: 0.0 to 1.0
- 0.0 = Strong negative intent ("I hate this")
- 0.5 = Neutral ("Meh, I don't know")
- 1.0 = Strong positive intent ("I love this")

#### Full Projection Method (Optional Enhancement)

For better accuracy, project the response onto the semantic axis:

```python
def calculate_ssr_projection(response_vec, pos_vec, neg_vec):
    """
    Full projection-based SSR.

    Projects the response vector onto the semantic axis,
    then normalizes based on anchor positions.

    Formula:
    axis = pos_vec - neg_vec
    projection = (response_vec · axis) / ||axis||²
    score = projection normalized to [0, 1]
    """
    axis = pos_vec - neg_vec
    axis_norm_sq = np.dot(axis, axis)

    if axis_norm_sq == 0:
        return 0.5  # Fallback to neutral

    # Project response onto axis
    projection = np.dot(response_vec - neg_vec, axis) / axis_norm_sq

    # Clamp to [0, 1] (responses outside anchor range)
    score = np.clip(projection, 0.0, 1.0)

    return score
```

**Use Case**:
- More accurate when responses are extreme (beyond anchors)
- Handles "I absolutely love this!" better than simplified method

---

### Step 5: Scale Transformation (Optional)

Convert from [0, 1] to more interpretable scales:

#### 1-5 Likert Scale
```python
def to_likert_5(ssr_score):
    """Convert SSR score to 1-5 scale."""
    return 1 + (ssr_score * 4)  # Maps [0,1] -> [1,5]
```

#### 0-100 Percentage Scale
```python
def to_percentage(ssr_score):
    """Convert SSR score to 0-100 percentage."""
    return ssr_score * 100
```

#### 0-10 Scale
```python
def to_scale_10(ssr_score):
    """Convert SSR score to 0-10 scale."""
    return ssr_score * 10
```

---

## Complete Reference Implementation

```python
import numpy as np
from typing import Tuple

class SSRCalculator:
    """
    Semantic Similarity Rating calculator.

    Converts free-text responses into numerical purchase intent scores
    using embedding similarity to semantic anchors.
    """

    def __init__(
        self,
        pos_anchor: str = "I would definitely buy this product.",
        neg_anchor: str = "I would never buy this product.",
        embedding_fn=None
    ):
        """
        Initialize calculator with anchor texts.

        Args:
            pos_anchor: Positive anchor text
            neg_anchor: Negative anchor text
            embedding_fn: Function that takes text and returns np.array
        """
        self.pos_anchor_text = pos_anchor
        self.neg_anchor_text = neg_anchor
        self.embedding_fn = embedding_fn

        # Pre-compute anchor embeddings (cache)
        self.pos_vec = None
        self.neg_vec = None

    def initialize_anchors(self):
        """Compute and cache anchor embeddings."""
        if self.embedding_fn is None:
            raise ValueError("Embedding function not set")

        self.pos_vec = self.embedding_fn(self.pos_anchor_text)
        self.neg_vec = self.embedding_fn(self.neg_anchor_text)

    @staticmethod
    def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot / (norm_a * norm_b))

    def calculate_simple(self, response_vec: np.ndarray) -> float:
        """
        Calculate SSR using simplified method.

        Args:
            response_vec: Embedding of the response text

        Returns:
            SSR score in [0, 1]
        """
        if self.pos_vec is None:
            raise ValueError("Anchors not initialized. Call initialize_anchors() first.")

        sim_pos = self.cosine_similarity(response_vec, self.pos_vec)

        # Normalize from [-1, 1] to [0, 1]
        score = (sim_pos + 1) / 2

        return score

    def calculate_projection(self, response_vec: np.ndarray) -> float:
        """
        Calculate SSR using full projection method.

        Args:
            response_vec: Embedding of the response text

        Returns:
            SSR score in [0, 1]
        """
        if self.pos_vec is None or self.neg_vec is None:
            raise ValueError("Anchors not initialized.")

        axis = self.pos_vec - self.neg_vec
        axis_norm_sq = np.dot(axis, axis)

        if axis_norm_sq == 0:
            return 0.5  # Neutral fallback

        # Project onto axis
        projection = np.dot(response_vec - self.neg_vec, axis) / axis_norm_sq

        # Clamp to [0, 1]
        score = float(np.clip(projection, 0.0, 1.0))

        return score

    def calculate_batch(
        self,
        response_vecs: np.ndarray,
        method: str = "simple"
    ) -> np.ndarray:
        """
        Calculate SSR for multiple responses (vectorized).

        Args:
            response_vecs: Array of shape (N, embedding_dim)
            method: "simple" or "projection"

        Returns:
            Array of SSR scores, shape (N,)
        """
        if method == "simple":
            # Vectorized cosine similarity
            dots = np.dot(response_vecs, self.pos_vec)
            norms_resp = np.linalg.norm(response_vecs, axis=1)
            norm_pos = np.linalg.norm(self.pos_vec)

            sims = dots / (norms_resp * norm_pos + 1e-10)
            scores = (sims + 1) / 2

            return scores

        elif method == "projection":
            axis = self.pos_vec - self.neg_vec
            axis_norm_sq = np.dot(axis, axis)

            if axis_norm_sq == 0:
                return np.full(len(response_vecs), 0.5)

            # Project all responses onto axis
            centered = response_vecs - self.neg_vec
            projections = np.dot(centered, axis) / axis_norm_sq

            scores = np.clip(projections, 0.0, 1.0)
            return scores

        else:
            raise ValueError(f"Unknown method: {method}")
```

---

## Validation Tests

### Test 1: Known Responses
```python
def test_ssr_known_responses():
    """Validate SSR with known positive/negative responses."""
    calculator = SSRCalculator(embedding_fn=get_embedding)
    calculator.initialize_anchors()

    # Positive response should score high
    pos_response = "This is exactly what I need! I'm buying it now."
    pos_vec = get_embedding(pos_response)
    score_pos = calculator.calculate_simple(pos_vec)
    assert score_pos > 0.7, f"Expected high score, got {score_pos}"

    # Negative response should score low
    neg_response = "This looks terrible and overpriced. No way."
    neg_vec = get_embedding(neg_response)
    score_neg = calculator.calculate_simple(neg_vec)
    assert score_neg < 0.3, f"Expected low score, got {score_neg}"

    # Neutral response should be mid-range
    neu_response = "I'm not sure. It has some good features but also drawbacks."
    neu_vec = get_embedding(neu_response)
    score_neu = calculator.calculate_simple(neu_vec)
    assert 0.4 < score_neu < 0.6, f"Expected neutral score, got {score_neu}"
```

### Test 2: Variance Check
```python
def test_ssr_variance():
    """Ensure SSR produces varied scores (not central tendency)."""
    responses = [
        "I love this!",
        "Pretty good, might buy.",
        "Meh, not really interested.",
        "This is awful.",
        "Exactly what I was looking for!"
    ]

    scores = [calculate_ssr(r) for r in responses]
    std_dev = np.std(scores)

    assert std_dev > 0.1, f"Scores too clustered: std={std_dev}"
```

### Test 3: Anchor Similarity
```python
def test_anchor_extremes():
    """Positive anchor should score ~1.0, negative ~0.0."""
    calculator = SSRCalculator(embedding_fn=get_embedding)
    calculator.initialize_anchors()

    # Positive anchor should score very high
    score_pos_anchor = calculator.calculate_simple(calculator.pos_vec)
    assert score_pos_anchor > 0.95

    # Negative anchor should score very low
    score_neg_anchor = calculator.calculate_simple(calculator.neg_vec)
    assert score_neg_anchor < 0.05
```

---

## Edge Cases

### Response Contains Numbers
**Problem**: LLM outputs "I'd rate this 4/5"
**Solution**: Validation layer rejects, retries with stronger prompt

### Empty Response
**Problem**: LLM returns empty string
**Solution**: Return neutral score (0.5) with warning flag

### Very Long Response
**Problem**: 500-word essay about the product
**Solution**: Embedding handles it (truncate to token limit if needed)

### Embedding Dimension Mismatch
**Problem**: Anchor is 1536-dim, response is 768-dim
**Solution**: Fail fast, enforce same embedding model

---

## Performance Optimization

### Batch Processing
Instead of calculating SSR one-by-one:
```python
# Slow (N API calls)
for response in responses:
    vec = get_embedding(response)
    score = calculator.calculate_simple(vec)

# Fast (1 API call + vectorized math)
vecs = get_embeddings_batch(responses)  # Shape: (N, 1536)
scores = calculator.calculate_batch(vecs)  # Shape: (N,)
```

### Caching Anchors
Anchor embeddings never change - compute once, reuse forever:
```python
# On app startup
calculator.initialize_anchors()  # Computed once

# During survey (no re-embedding of anchors)
for response_vec in response_vecs:
    score = calculator.calculate_simple(response_vec)
```

---

## Alternative Anchor Texts (Experimental)

The paper suggests these can be tuned:

```python
# More extreme (may increase variance)
POSITIVE_ANCHOR = "This is the best product I've ever seen. I'm buying it immediately."
NEGATIVE_ANCHOR = "This is completely useless. I would never waste money on this."

# More neutral (may reduce variance)
POSITIVE_ANCHOR = "I would purchase this product."
NEGATIVE_ANCHOR = "I would not purchase this product."

# Domain-specific (e.g., B2B software)
POSITIVE_ANCHOR = "This tool would significantly improve our workflow. We should adopt it."
NEGATIVE_ANCHOR = "This tool doesn't fit our needs. We won't be using it."
```

**Recommendation**: Start with default anchors from paper, experiment later.

---

## Debugging Checklist

- [ ] Anchor embeddings are non-zero vectors
- [ ] Cosine similarity returns values in [-1, 1]
- [ ] SSR scores are in [0, 1]
- [ ] Positive responses score >0.5
- [ ] Negative responses score <0.5
- [ ] Standard deviation of scores >0.1
- [ ] No NaN or Inf values in calculations

---

**Next Steps**: Read [persona-generation.md](persona-generation.md) for the persona system specification.
