# Project Overview - SSR Market Research Tool

## What You're Building

A **Minimum Viable Product (MVP)** that automates consumer purchase intent research using:
- Large Language Models (LLMs) for synthetic personas
- Semantic Similarity Rating (SSR) algorithm
- Vector embeddings for measuring intent

**Goal**: Replace expensive human surveys with AI-generated data that achieves >0.9 correlation with real consumer behavior.

---

## The Problem This Solves

### Traditional Market Research Problems:
1. **Slow**: Takes weeks to recruit participants
2. **Expensive**: $50-100 per respondent
3. **Limited**: Hard to test multiple concepts quickly

### LLM Survey Problems (Before SSR):
1. **Central Tendency Bias**: LLMs cluster responses around "3" on a 1-5 scale
2. **Low Variance**: All scores look the same
3. **Poor Correlation**: Doesn't match human behavior

### SSR Solution:
1. **Fast**: 100 respondents in 2 minutes
2. **Cheap**: <$1 per 100 respondents
3. **Accurate**: >0.9 correlation with humans
4. **Varied**: Produces diverse, realistic scores

---

## How SSR Works (High-Level)

### Traditional LLM Survey (Wrong)
```
Input: "Rate this product 1-5"
Output: "3" ← Central tendency bias!
```

### SSR Method (Right)
```
Step 1: Ask for natural language opinion
Input: "Would you buy this product? Explain why."
Output: "It looks useful but too expensive for my budget..."

Step 2: Convert text to vector (embedding)
Response → [0.23, -0.45, 0.89, ..., 0.12] (1536 numbers)

Step 3: Measure similarity to semantic anchors
Positive anchor: "I would definitely buy this product."
Negative anchor: "I would never buy this product."

Cosine similarity to positive anchor = 0.42

Step 4: Calculate final score
SSR Score = (0.42 + 1) / 2 = 0.71
Normalized to 1-10 scale = 7.1/10
```

**Key Insight**: By avoiding explicit numeric questions, we bypass the central tendency bias.

---

## System Components

### 1. Persona Generator
**What**: Creates synthetic respondents with realistic demographics
**Input**: Demographics constraints (age, gender, income, etc.)
**Output**: 100 unique personas like:
- "28-year-old female software engineer in Seoul, interests: gaming, tech"
- "55-year-old male teacher in New York, interests: reading, gardening"

**Why**: Different demographics have different purchase patterns

---

### 2. LLM Survey Executor
**What**: Collects free-text opinions from each persona
**Input**: Persona + Product description
**Output**: Natural language response (NO numbers allowed)

**Example**:
```
Persona: 28-year-old software engineer
Product: "Smart coffee mug that keeps drinks hot for 8 hours"
Response: "This would be perfect for my long coding sessions!
I hate microwaving cold coffee. A bit pricey, but I'd definitely
consider buying it."
```

**Critical Constraint**: Prompt must FORBID numeric ratings

---

### 3. Embedding Service
**What**: Converts text to dense vectors
**Input**: Text string
**Output**: 1536-dimensional vector

**Technical**:
- Uses OpenAI `text-embedding-3-small` model
- Batch processing for efficiency (100 texts at once)
- Caches frequently used embeddings (anchors)

---

### 4. SSR Calculator
**What**: Implements the core SSR algorithm
**Input**:
- Response embedding (1536-dim vector)
- Positive anchor embedding
- Negative anchor embedding

**Output**: SSR score (0.0 to 1.0)

**Math**:
```python
def calculate_ssr(response_vec, pos_anchor_vec):
    # Cosine similarity: dot product / (norm A × norm B)
    similarity = np.dot(response_vec, pos_anchor_vec) / (
        np.linalg.norm(response_vec) * np.linalg.norm(pos_anchor_vec)
    )

    # Normalize from [-1, 1] to [0, 1]
    score = (similarity + 1) / 2

    return score
```

---

### 5. Aggregator & Reporter
**What**: Summarizes results across all personas
**Input**: List of (persona, response, score) tuples
**Output**:
- Mean score (e.g., 7.2/10)
- Standard deviation (variance check)
- Distribution histogram
- Top/bottom quotes
- Cost breakdown

---

## Data Flow (Complete Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                               │
│    - Product: "AI meal planning app"                        │
│    - Demographics: Age 25-45, Income: Medium-High           │
│    - Sample Size: 100                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PERSONA GENERATION                                       │
│    Generate 100 diverse personas:                           │
│    - Random sampling from templates                         │
│    - Consistency validation (e.g., no 20-year-old retirees) │
│    - Convert to system prompts for LLM                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. LLM SURVEY (Parallel Processing)                        │
│    For each persona:                                        │
│    - Construct anti-numeric prompt                          │
│    - Call OpenAI GPT-4o-mini                                │
│    - Validate response (no numbers)                         │
│    - Retry if invalid (max 3 times)                         │
│    Result: 100 free-text opinions                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. EMBEDDING CONVERSION (Batched)                          │
│    Batch 1: Embed responses 1-100                           │
│    (Single API call, ~500ms)                                │
│    Cache: Embed anchors (computed once)                     │
│    Result: 100 response vectors + 2 anchor vectors          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. SSR CALCULATION (Vectorized)                            │
│    For each response vector:                                │
│    - Calculate cosine similarity to pos_anchor              │
│    - Normalize to [0, 1] scale                              │
│    Result: 100 SSR scores                                   │
└──────────────��─┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. AGGREGATION & REPORTING                                 │
│    Statistics:                                              │
│    - Mean: 7.2/10                                           │
│    - Std Dev: 1.4 (variance check ✓)                       │
│    - Min: 3.1, Max: 9.8                                     │
│    Visualization:                                           │
│    - Histogram of score distribution                        │
│    - Top 5 positive quotes                                  │
│    - Bottom 5 negative quotes                               │
│    Cost: $0.52 total                                        │
└─────────────────────────────────────────────────────────────┘
```

**Total Time**: ~2 minutes for 100 respondents

---

## Key Technical Decisions

### 1. LLM Model: GPT-5.2 (or gpt-5-mini)
**Why**:
- Best general-purpose model with improved intelligence
- Configurable reasoning effort (none/low/medium/high/xhigh)
- Excellent instruction following and accuracy
- Uses Responses API for better context management
- gpt-5-mini: Cost-optimized alternative

**Alternative**: gpt-5-nano for high-throughput simple tasks

---

### 2. Embedding Model: text-embedding-3-small
**Why**:
- Industry standard (1536 dimensions)
- High quality for semantic tasks
- Cost-effective ($0.02 per 1M tokens)
- Deterministic (same input → same output)

**Alternative**: Local `sentence-transformers` (free, but lower quality)

---

### 3. Reasoning Effort: "none" + Verbosity: "medium"
**Why**:
- **reasoning="none"**: Fast responses, critical for variance
- **verbosity="medium"**: Balanced output length
- Higher reasoning effort can reduce response diversity
- GPT-5.2 note: temperature not supported with reasoning effort > none
- For varied responses: use reasoning="none" with prompt engineering

---

### 4. Semantic Anchors
```python
POSITIVE_ANCHOR = "I would definitely buy this product."
NEGATIVE_ANCHOR = "I would never buy this product."
```

**Why these specific texts**:
- Simple, unambiguous
- Clear directional intent
- Validated in paper to maximize cosine distance
- Language matches natural responses

---

## Success Metrics

### 1. Variance (Most Important!)
**Requirement**: Standard deviation > 0.5
**Why**: Low variance indicates central tendency bias (SSR failed)

**Example**:
```
Good Distribution:
Scores: [2.1, 3.5, 6.8, 7.2, 8.9, 9.1, ...]
Std Dev: 1.42 ✓

Bad Distribution (Central Tendency):
Scores: [4.9, 5.0, 5.1, 5.0, 4.8, 5.2, ...]
Std Dev: 0.12 ✗ (SSR algorithm broken!)
```

---

### 2. Cost
**Requirement**: <$1.00 per 100 respondents

**Breakdown**:
- LLM responses (100 × ~150 tokens): ~$0.50
- Embeddings (100 texts + 2 anchors): ~$0.02
- Total: **$0.52** ✓

---

### 3. Speed
**Requirement**: <2 minutes for N=100

**Breakdown**:
- Persona generation: <1 second (template-based)
- LLM responses (parallel): ~1 minute
- Embeddings (batched): ~10 seconds
- SSR calculation (vectorized): <1 second
- Total: **~1.5 minutes** ✓

---

### 4. Correlation (Validation Phase)
**Requirement**: >0.9 correlation with human data
**How to validate**:
1. Run SSR survey on known product concepts
2. Compare to human survey data (from paper)
3. Calculate Pearson correlation coefficient

**Note**: MVP can skip this (paper already validated)

---

## File Structure (What You'll Create)

```
my-project/
├── .env                    # API keys (gitignored)
├── .env.example            # Template for API keys
├── .gitignore              # Exclude .env, cache, etc.
├── requirements.txt        # Python dependencies
├── README.md               # User documentation ✓
├── PROMPT.md               # Dev instructions ✓
├── fix_plan.md             # Implementation tasks ✓
│
├── specs/                  # Technical specifications ✓
│   ├── OVERVIEW.md         # This file
│   ├── architecture.md     # System design
│   ├── ssr-algorithm.md    # Math details
│   ├── persona-generation.md
│   └── api-design.md
│
├── src/                    # Source code (TO BE BUILT)
│   ├── __init__.py
│   ├── ssr/
│   │   ├── calculator.py   # Core SSR math
│   │   ├── anchors.py      # Anchor definitions
│   │   └── utils.py        # Cosine similarity
│   ├── personas/
│   │   ├── generator.py    # Persona creation
│   │   ├── templates.py    # Demographic templates
│   │   └── validator.py    # Consistency checks
│   ├── embeddings/
│   │   ├── service.py      # OpenAI API wrapper
│   │   └── cache.py        # Embedding cache
│   ├── survey/
│   │   ├── executor.py     # LLM API integration
│   │   ├── prompts.py      # Prompt templates
│   │   └── validator.py    # Response validation
│   ├── reporting/
│   │   ├── aggregator.py   # Statistics
│   │   ├── visualizer.py   # Charts
│   │   └── exporter.py     # CSV export
│   └── ui/
│       └── app.py          # Streamlit web UI
│
├── tests/                  # Test suite (TO BE BUILT)
│   ├── test_ssr.py
│   ├── test_personas.py
│   ├── test_embeddings.py
│   ├── test_survey.py
│   ├── test_reporting.py
│   └── fixtures/
│       ├── sample_responses.json
│       └── cached_embeddings.pkl
│
└── examples/               # Sample data (TO BE BUILT)
    ├── product_concepts.json
    └── expected_results.json
```

---

## Implementation Priority

### Phase 1: Core Engine (MUST HAVE)
1. Project setup (dependencies, .env)
2. SSR algorithm (math functions)
3. Embedding service (OpenAI API)
4. Persona generation (template-based)
5. Survey executor (LLM API)
6. End-to-end pipeline (orchestration)
7. Basic tests (validate variance)

**Deliverable**: CLI that accepts product description, outputs SSR scores

---

### Phase 2: User Interface (NICE TO HAVE)
1. Streamlit web app (forms, charts)
2. CSV export
3. Cost tracking dashboard

**Deliverable**: Web UI for non-technical users

---

### Phase 3: Polish (OPTIONAL)
1. A/B testing mode
2. Custom anchors
3. Qualitative analysis (theme extraction)
4. Performance optimization (async LLM calls)

**Deliverable**: Production-ready tool

---

## Common Pitfalls to Avoid

### 1. Temperature Too Low
**Symptom**: All scores near 0.5
**Cause**: LLM generating similar responses
**Fix**: Set temperature to 0.7 (not 0.0)

---

### 2. Numeric Prompts
**Symptom**: Responses like "I'd rate this 4/5"
**Cause**: Prompt doesn't forbid numbers
**Fix**: Add explicit constraint: "Do NOT use numbers"

---

### 3. Wrong Embedding Model
**Symptom**: Scores don't correlate with intuition
**Cause**: Using different models for responses vs anchors
**Fix**: Use same model for all embeddings

---

### 4. No Caching
**Symptom**: Slow performance, high costs
**Cause**: Re-computing anchor embeddings every time
**Fix**: Cache anchor embeddings (they never change)

---

### 5. Sequential Processing
**Symptom**: Takes 10 minutes for 100 respondents
**Cause**: LLM calls in a loop (sequential)
**Fix**: Use parallel/async processing

---

## Quick Reference: Key Formulas

### Cosine Similarity
```python
cosine_sim = np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B))
```
Range: [-1, 1]
- 1 = identical direction
- 0 = orthogonal
- -1 = opposite direction

---

### SSR Score (Simplified)
```python
ssr_score = (cosine_similarity(response, pos_anchor) + 1) / 2
```
Range: [0, 1]
- 0 = Strong negative intent
- 0.5 = Neutral
- 1 = Strong positive intent

---

### Scale Transformation
```python
# To 1-5 Likert
score_5 = 1 + (ssr_score * 4)

# To 0-10 scale
score_10 = ssr_score * 10

# To percentage
score_pct = ssr_score * 100
```

---

## Getting Started Checklist

- [ ] Read [README.md](../README.md) for project overview
- [ ] Read [PROMPT.md](../PROMPT.md) for dev instructions
- [ ] Review [architecture.md](architecture.md) for system design
- [ ] Study [ssr-algorithm.md](ssr-algorithm.md) for math details
- [ ] Check [fix_plan.md](../fix_plan.md) for tasks
- [ ] Set up Python environment (venv, dependencies)
- [ ] Get OpenAI API key
- [ ] Start with Phase 1, Task 1 (Project Setup)

---

## Questions to Ask Yourself

### Before Starting:
1. Do I understand why SSR avoids central tendency bias?
2. Do I know what "embedding" means?
3. Do I know what "cosine similarity" measures?

### During Implementation:
1. Am I using the correct temperature (0.7)?
2. Are my prompts forbidding numeric ratings?
3. Am I caching anchor embeddings?
4. Are my scores showing variance (std dev > 0.5)?

### After Implementation:
1. Does a positive product get a high score?
2. Does a negative product get a low score?
3. Is the cost <$1 per 100 respondents?
4. Is the speed <2 minutes for 100 respondents?

---

## Resources

- **Paper**: [arXiv:2510.08338](https://arxiv.org/html/2510.08338v3)
- **OpenAI API Docs**: [platform.openai.com/docs](https://platform.openai.com/docs)
- **Cosine Similarity Explanation**: [Wikipedia](https://en.wikipedia.org/wiki/Cosine_similarity)
- **Embeddings Tutorial**: [OpenAI Guide](https://platform.openai.com/docs/guides/embeddings)

---

**You're ready to build!** Start with [fix_plan.md](../fix_plan.md) and tackle Phase 1 tasks in order.
