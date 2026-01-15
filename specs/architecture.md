# System Architecture

## Overview
The SSR Market Research Tool follows a **pipeline architecture** with four main stages:
1. Persona Generation
2. Response Collection
3. Semantic Similarity Calculation
4. Aggregation & Reporting

## High-Level Data Flow

```
┌─────────────────┐
│  User Input     │
│ - Product Desc  │
│ - Demographics  │
│ - Sample Size   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Persona Generator       │
│ - Creates N personas    │
│ - Enforces demographics │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ LLM Survey Executor     │
│ - Gets free-text        │
│ - NO numeric prompts    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Embedding Service       │
│ - Vectorize responses   │
│ - Vectorize anchors     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ SSR Calculator          │
│ - Cosine similarity     │
│ - Projection formula    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Aggregator & Reporter   │
│ - Mean/Median scores    │
│ - Distribution charts   │
│ - Qualitative themes    │
└─────────────────────────┘
```

## Component Breakdown

### 1. Persona Generator (`src/personas/`)
**Responsibility**: Create diverse synthetic respondents

**Inputs**:
- Demographics profile (Age, Gender, Income, etc.)
- Sample size (N)

**Outputs**:
- List of persona dictionaries with attributes
- System prompts enforcing persona identity

**Key Files**:
- `generator.py`: Core persona creation logic
- `templates.py`: Persona attribute templates
- `validator.py`: Ensures demographic diversity

**Design Decisions**:
- Use stratified sampling to ensure demographic spread
- Personas must include: age, gender, occupation, location, interests
- Each persona gets a unique ID for tracking

---

### 2. LLM Survey Executor (`src/survey/`)
**Responsibility**: Collect free-text purchase opinions

**Inputs**:
- Persona system prompt
- Product concept description

**Outputs**:
- Free-text response (no numbers allowed)
- Metadata (tokens used, cost, latency)

**Key Files**:
- `executor.py`: LLM API integration
- `prompts.py`: Prompt templates with anti-numeric constraints
- `validator.py`: Ensures responses are valid (no scores)

**Prompt Template**:
```
System: You are a {age}-year-old {gender} {occupation} living in {location}.
You are interested in {interests}.

User: Here is a product concept:
"{product_description}"

Based on this description, explain your thoughts on whether you would
purchase this product. Focus on your reasoning, not a rating.
DO NOT provide a numerical score. Just explain your opinion naturally.
```

**Critical Constraint**:
- Responses containing digits, "out of 10", "rating", etc. must be rejected

---

### 3. Embedding Service (`src/embeddings/`)
**Responsibility**: Convert text to vector representations

**Inputs**:
- Text strings (responses, anchors)

**Outputs**:
- NumPy arrays (embedding vectors)

**Key Files**:
- `service.py`: Wrapper for OpenAI/HuggingFace APIs
- `cache.py`: Cache frequently used embeddings (anchors)

**Model Selection**:
- Primary: `text-embedding-3-small` (OpenAI) - cost-effective
- Fallback: `all-MiniLM-L6-v2` (local) - for offline testing

**Optimization**:
- Batch embed responses (up to 100 at once)
- Cache anchor embeddings (only compute once)

---

### 4. SSR Calculator (`src/ssr/`)
**Responsibility**: Implement the core SSR algorithm

**Inputs**:
- Response embeddings
- Positive anchor embedding
- Negative anchor embedding

**Outputs**:
- SSR score (float between 0 and 1)

**Key Files**:
- `calculator.py`: Core SSR math
- `anchors.py`: Anchor text definitions
- `utils.py`: Vector operations (cosine similarity, normalization)

**Algorithm** (see [ssr-algorithm.md](ssr-algorithm.md) for details):
```python
def calculate_ssr(response_vec, pos_anchor_vec, neg_anchor_vec):
    # 1. Define semantic axis
    axis = pos_anchor_vec - neg_anchor_vec

    # 2. Calculate cosine similarity to positive anchor
    sim_pos = cosine_similarity(response_vec, pos_anchor_vec)

    # 3. Normalize to 0-1 scale
    score = (sim_pos + 1) / 2  # Simplified projection

    return score
```

---

### 5. Aggregator & Reporter (`src/reporting/`)
**Responsibility**: Summarize results and generate insights

**Inputs**:
- List of (persona, response, score) tuples

**Outputs**:
- Statistical summary (mean, median, std dev)
- Distribution histogram
- Top/bottom quotes
- CSV export

**Key Files**:
- `aggregator.py`: Statistical computations
- `visualizer.py`: Chart generation (matplotlib/plotly)
- `exporter.py`: CSV/JSON export

**Metrics to Track**:
- Average purchase intent (0-100 scale)
- Standard deviation (MUST be >0.5 for validity)
- Score distribution (histogram with 10 bins)
- Cost per respondent

---

## Technology Choices

### LLM Provider
**Primary**: OpenAI GPT-4o-mini
- **Rationale**: Best cost/performance for text generation
- **Cost**: ~$0.15 per 1M input tokens, $0.60 per 1M output
- **Fallback**: Anthropic Claude Haiku (if quota issues)

### Embedding Model
**Primary**: OpenAI `text-embedding-3-small`
- **Rationale**: Industry standard, 1536 dimensions
- **Cost**: ~$0.02 per 1M tokens
- **Fallback**: Local `sentence-transformers` for testing

### Data Processing
- **Pandas**: Survey data tables
- **NumPy**: Vector operations
- **Scikit-learn**: Cosine similarity utilities

### UI Framework
- **Streamlit**: Fastest path to interactive web UI
- **Plotly**: Interactive charts
- **Alternative**: CLI with rich text output

---

## Error Handling Strategy

### LLM API Failures
- Retry with exponential backoff (max 3 attempts)
- Switch to fallback model if primary unavailable
- Log all API errors with request context

### Invalid Responses
- Reject responses containing numbers
- Retry with stronger anti-numeric prompt
- Max 2 retries per persona before skipping

### Embedding Failures
- Cache successful embeddings
- Batch operations to reduce API calls
- Graceful degradation (skip failed embeddings, continue)

---

## Performance Requirements

### Speed
- **Target**: <2 minutes for N=100 respondents
- **Breakdown**:
  - Persona generation: <1 second
  - LLM responses: ~1 minute (parallel requests)
  - Embeddings: ~10 seconds (batched)
  - SSR calculation: <1 second

### Cost
- **Target**: <$1.00 per 100 respondents
- **Estimated**:
  - LLM calls: ~$0.50 (100 × 150 tokens avg)
  - Embeddings: ~$0.02 (100 responses + 2 anchors)
  - Total: ~$0.52 (well under budget)

### Scalability
- Support up to 1000 respondents in MVP
- Use async/await for parallel LLM calls
- Stream results as they complete (for UI responsiveness)

---

## Security & Privacy

### API Keys
- Load from `.env` file (never hardcode)
- Use `python-dotenv` for environment management

### Data Storage
- Do NOT persist user product concepts by default
- Offer opt-in CSV export only
- Clear temporary data after session

### Rate Limiting
- Respect OpenAI rate limits (3500 RPM for tier 1)
- Implement token bucket algorithm if needed

---

## Testing Architecture

### Unit Tests
- SSR math functions (deterministic)
- Persona generation logic
- Vector operations

### Integration Tests
- LLM API calls (with mocking via `responses` library)
- Embedding API calls (with cached fixtures)

### End-to-End Tests
- Full pipeline with 10 synthetic respondents
- Validate score variance
- Check cost tracking accuracy

### Fixtures
- Known product concepts with expected score ranges
- Pre-computed embeddings for regression testing

---

## Future Enhancements (Not in MVP)

1. **Multi-language Support**: Non-English product concepts
2. **Custom Anchors**: User-defined positive/negative texts
3. **Historical Tracking**: Save and compare past surveys
4. **Advanced Analytics**: Sentiment analysis, topic modeling
5. **API Mode**: RESTful API for programmatic access

---

## File Tree (Concrete)

```
my-project/
├── .env                          # API keys (gitignored)
├── .gitignore
├── requirements.txt
├── README.md
├── PROMPT.md
├── @fix_plan.md
├── specs/
│   ├── architecture.md          # This file
│   ├── ssr-algorithm.md         # Math details
│   ├── persona-generation.md    # Persona specs
│   └── api-design.md            # LLM/Embedding API specs
├── src/
│   ├── __init__.py
│   ├── personas/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── templates.py
│   │   └── validator.py
│   ├── survey/
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   ├── prompts.py
│   │   └── validator.py
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── cache.py
│   ├── ssr/
│   │   ├── __init__.py
│   │   ├── calculator.py
│   │   ├── anchors.py
│   │   └── utils.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── aggregator.py
│   │   ├── visualizer.py
│   │   └── exporter.py
│   └── ui/
│       ├── __init__.py
│       └── app.py               # Streamlit entrypoint
├── tests/
│   ├── __init__.py
│   ├── test_personas.py
│   ├── test_survey.py
│   ├── test_embeddings.py
│   ├── test_ssr.py
│   ├── test_reporting.py
│   └── fixtures/
│       ├── sample_responses.json
│       └── cached_embeddings.pkl
└── examples/
    ├── product_concepts.json    # Sample inputs
    └── expected_results.json    # Validation data
```

---

**Next Steps**: Read [ssr-algorithm.md](ssr-algorithm.md) for the mathematical specification.
