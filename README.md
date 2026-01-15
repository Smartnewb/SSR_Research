# SSR Market Research Tool

> **Synthetic consumer research powered by semantic similarity**

Generate realistic purchase intent data for product concepts using LLMs and the Semantic Similarity Rating (SSR) method.

Based on: *"LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings"* ([arXiv:2510.08338](https://arxiv.org/html/2510.08338v3))

---

## What is SSR?

Traditional survey method (❌ Biased):
```
LLM: "Rate this product 1-5"
→ Response: "3" (central tendency bias)
```

SSR method (✅ Accurate):
```
LLM: "Explain your opinion naturally"
→ Response: "It looks useful but too expensive for my budget..."
→ Embedding similarity to "I would buy": 0.42
→ Final Score: 4.2/10 (>0.9 correlation with humans)
```

---

## Key Features

- **No Central Tendency Bias**: Free-text responses avoid clustering around middle
- **High Correlation**: >0.9 with human purchase intent (validated in paper)
- **Cost-Effective**: <$1 per 100 synthetic respondents
- **Fast**: Results in <2 minutes
- **Diverse**: Generates personas across demographics

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repo-url>
cd my-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

Get an API key from: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 3. Run Example

```bash
# CLI usage
python -m src.cli \
  --product "Smart coffee mug that keeps drinks hot for 8 hours" \
  --sample-size 50 \
  --output results.csv

# Web UI (Streamlit)
streamlit run src/ui/app.py
```

---

## How It Works

### Architecture

```
User Input → Persona Generation → LLM Survey → Embedding → SSR Calculation → Results
```

1. **Persona Generation**: Create synthetic respondents with demographics
2. **LLM Survey**: Collect free-text opinions (NO numeric prompts)
3. **Embedding**: Convert responses to vectors
4. **SSR Calculation**: Measure similarity to semantic anchors
5. **Aggregation**: Statistical summary + visualizations

### The SSR Algorithm

```python
# Define semantic anchors
pos_anchor = "I would definitely buy this product."
neg_anchor = "I would never buy this product."

# Get embeddings
response_vec = embed(user_response)
pos_vec = embed(pos_anchor)

# Calculate similarity
similarity = cosine_similarity(response_vec, pos_vec)

# Normalize to [0, 1] scale
ssr_score = (similarity + 1) / 2
```

See [specs/ssr-algorithm.md](specs/ssr-algorithm.md) for mathematical details.

---

## Usage Examples

### Example 1: Test a Product Concept

```python
from src.pipeline import run_survey

result = run_survey(
    product_description="AI-powered meal planning app with grocery delivery",
    demographics={
        "age_range": [25, 45],
        "income_bracket": ["Medium", "High"]
    },
    sample_size=100
)

print(f"Average Purchase Intent: {result.mean_score:.1f}/10")
print(f"Standard Deviation: {result.std_dev:.2f}")
print(f"Total Cost: ${result.total_cost:.2f}")
```

**Output**:
```
Average Purchase Intent: 6.8/10
Standard Deviation: 1.42
Total Cost: $0.52
```

### Example 2: A/B Test Two Products

```python
from src.pipeline import compare_products

winner = compare_products(
    product_a="Basic meal kit delivery",
    product_b="AI-customized meal kit with dietary tracking",
    sample_size=50
)

print(f"Winner: {winner.product_name}")
print(f"Score Difference: {winner.score_delta:.1f} points")
```

---

## Project Structure

```
my-project/
├── specs/              # Technical specifications
│   ├── architecture.md
│   ├── ssr-algorithm.md
│   ├── persona-generation.md
│   └── api-design.md
├── src/
│   ├── ssr/           # Core SSR algorithm
│   ├── personas/      # Persona generation
│   ├── embeddings/    # Embedding service
│   ├── survey/        # LLM survey executor
│   ├── reporting/     # Analytics & visualization
│   └── ui/            # Streamlit web app
├── tests/             # pytest test suite
├── examples/          # Sample product concepts
├── PROMPT.md          # Development instructions
├── fix_plan.md        # Implementation roadmap
└── README.md          # This file
```

---

## Configuration

Edit `.env` to customize behavior:

```bash
# API Keys
OPENAI_API_KEY=sk-...

# Model Selection
LLM_MODEL=gpt-5-mini               # Cost-optimized (or gpt-5.2 for best quality)
EMBEDDING_MODEL=text-embedding-3-small

# GPT-5.2 Behavior
REASONING_EFFORT=none              # none (fast) | low | medium | high | xhigh
VERBOSITY=medium                   # low | medium | high
MAX_OUTPUT_TOKENS=200              # Limit response length
ENABLE_CACHING=true                # Cache embeddings for speed
```

---

## Development

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/test_ssr.py

# Integration tests (requires API key)
pytest -m integration
```

### Check Coverage

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Code Style

```bash
# Format with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/
```

---

## Cost Breakdown

Based on OpenAI pricing (2025, GPT-5 family):

| Operation | Model | Cost per 100 |
|-----------|-------|-------------|
| LLM Responses | gpt-5-mini | ~$0.20 |
| LLM Responses | gpt-5.2 (reasoning=none) | ~$0.45 |
| Embeddings | text-embedding-3-small | ~$0.02 |
| **Total (gpt-5-mini)** | | **~$0.22** |
| **Total (gpt-5.2)** | | **~$0.47** |

**Optimization tips**:
- Use batch embedding (10x faster, same cost)
- Cache anchor embeddings (computed once)
- Lower `sample_size` for quick tests

---

## Roadmap

### Phase 1: Core Engine ✅ (In Progress)
- SSR algorithm implementation
- Persona generation
- LLM integration
- Basic CLI

### Phase 2: UI & UX
- Streamlit web interface
- CSV export
- Cost tracking dashboard

### Phase 3: Advanced Features
- Multi-language support
- Custom anchor texts
- Historical tracking
- Qualitative analysis (theme extraction)

See [fix_plan.md](fix_plan.md) for detailed tasks.

---

## Troubleshooting

### "Invalid API Key" Error
- Check `.env` file has `OPENAI_API_KEY=sk-...`
- Verify key at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Scores All Near 0.5 (Central Tendency)
- Ensure `REASONING_EFFORT=none` (reasoning can reduce variance)
- Adjust `VERBOSITY` to get more varied responses
- Check personas are diverse (not all identical)
- Verify responses don't contain numeric ratings

### Slow Performance
- Enable embedding cache (`ENABLE_CACHING=true`)
- Use batch processing for embeddings
- Lower `sample_size` for testing

### High Costs
- Switch to `gpt-5-mini` (cost-optimized model)
- Use `gpt-5-nano` for simple tasks
- Reduce `MAX_OUTPUT_TOKENS` to 150
- Keep `REASONING_EFFORT=none` (reasoning tokens are expensive)
- Use local embeddings for testing (`sentence-transformers`)

---

## Contributing

1. Read [PROMPT.md](PROMPT.md) for development guidelines
2. Check [fix_plan.md](fix_plan.md) for open tasks
3. Follow Python style guide (see `.claude/rules/python.md`)
4. Write tests for new features
5. Update documentation

---

## References

- **Paper**: [arXiv:2510.08338](https://arxiv.org/html/2510.08338v3)
- **OpenAI Embeddings**: [Docs](https://platform.openai.com/docs/guides/embeddings)
- **Streamlit**: [Docs](https://docs.streamlit.io/)

---

## License

MIT License (or specify your license)

---

## Contact

For questions or issues, please open a GitHub issue or contact [your email].

---

**Ready to start?** → Read [PROMPT.md](PROMPT.md) and check [fix_plan.md](fix_plan.md) for next steps.
