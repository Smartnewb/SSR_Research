# SSR Market Research Tool - Agent Instructions

## Build & Run Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run Tests
```bash
# All tests
python -m pytest tests/ -v

# Quick test
python -m pytest tests/ -q

# Specific module
python -m pytest tests/test_ssr.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Run Applications

#### Streamlit Web UI
```bash
streamlit run src/ui/app.py
```

#### CLI
```bash
# Basic usage (with mock data - no API needed)
python -m src.cli --product "Smart coffee mug" --sample-size 20 --mock

# Full usage (requires API key)
python -m src.cli --product "Smart coffee mug" --sample-size 50 --output results.csv

# With demographic targeting
python -m src.cli --product "Gaming laptop" --sample-size 30 --age-range 18-35 --gender Male Female

# JSON output
python -m src.cli --product "Test product" --sample-size 10 --mock --json

# A/B Testing (compare two products)
python -m src.cli --product "Smart mug at $79" --compare "Regular mug at $15" --name-a "Smart Mug" --name-b "Regular Mug" --sample-size 30 --mock
```

### Python API
```python
from src.pipeline import SSRPipeline

# Mock mode (no API calls)
pipeline = SSRPipeline()
results = pipeline.run_survey_mock(
    product_description="Smart coffee mug that keeps drinks hot",
    sample_size=20,
)
print(f"Mean Score: {results.mean_score:.2f}")

# Live mode (requires OPENAI_API_KEY)
pipeline = SSRPipeline(llm_model="gpt-4o-mini")
results = pipeline.run_survey(
    product_description="Smart coffee mug that keeps drinks hot",
    sample_size=50,
)

# A/B Testing
from src.ab_testing import run_ab_test

ab_result = run_ab_test(
    product_a="Smart mug that keeps drinks at perfect temperature",
    product_b="Regular insulated mug",
    sample_size=30,
    product_a_name="Smart Mug",
    product_b_name="Regular Mug",
    use_mock=True,
)
print(ab_result.summary())
```

## Project Structure

```
src/
├── ssr/              # Core SSR algorithm
│   ├── utils.py      # cosine_similarity, normalization
│   ├── anchors.py    # Semantic anchor definitions
│   └── calculator.py # SSRCalculator class
├── personas/         # Persona generation
│   ├── templates.py  # Demographic templates
│   ├── generator.py  # Persona generation functions
│   └── validator.py  # Coherence validation
├── embeddings/       # Embedding service
│   ├── service.py    # OpenAI embedding API
│   └── cache.py      # File-based caching
├── survey/           # Survey execution
│   ├── prompts.py    # Prompt templates
│   ├── executor.py   # LLM API calls
│   └── validator.py  # Response validation
├── reporting/        # Results aggregation
│   └── aggregator.py # Statistics & formatting
├── ui/               # Streamlit app
│   └── app.py        # Web interface
├── ab_testing.py     # A/B testing module
├── cli.py            # Command-line interface
└── pipeline.py       # End-to-end orchestration
```

## Key Classes

### SSRCalculator
```python
from src.ssr.calculator import SSRCalculator

calc = SSRCalculator(embedding_fn=my_embed_func)
calc.initialize_anchors()
score = calc.calculate_simple(response_embedding)  # Returns 0-1
```

### SSRPipeline
```python
from src.pipeline import SSRPipeline

pipeline = SSRPipeline(
    llm_model="gpt-4o-mini",
    embedding_model="text-embedding-3-small",
    enable_caching=True,
)
```

## Environment Variables

```bash
OPENAI_API_KEY=sk-...          # Required for live mode
LLM_MODEL=gpt-4o-mini          # Default LLM
EMBEDDING_MODEL=text-embedding-3-small
```

## Cost Estimates

| Sample Size | Model | Estimated Cost |
|-------------|-------|----------------|
| 10 | gpt-4o-mini | ~$0.05 |
| 50 | gpt-4o-mini | ~$0.25 |
| 100 | gpt-4o-mini | ~$0.50 |
| 100 | gpt-5-mini | ~$0.80 |

## Testing Notes

- Use `--mock` flag or `run_survey_mock()` for testing without API calls
- Mock mode uses random embeddings (lower variance than real)
- Integration test `test_real_survey_small` is skipped by default (requires API key)
- Run with `pytest -m integration` to include API tests

---

## Backend API (FastAPI)

### Run Backend Server
```bash
# Install backend dependencies
pip install fastapi uvicorn pydantic-settings httpx websockets

# Run development server
uvicorn backend.app.main:app --reload --port 8000

# Production server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Run Backend Tests
```bash
python -m pytest backend/tests/ -v
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/api/surveys` | Run survey |
| POST | `/api/surveys/compare` | A/B testing |
| WS | `/ws/surveys/{id}` | Real-time progress |

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Example API Request
```bash
# Run mock survey
curl -X POST http://localhost:8000/api/surveys \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Smart coffee mug that keeps your drink hot - $79",
    "sample_size": 10,
    "use_mock": true
  }'

# A/B Test
curl -X POST http://localhost:8000/api/surveys/compare \
  -H "Content-Type: application/json" \
  -d '{
    "product_a": "Smart mug - $79",
    "product_b": "Regular mug - $15",
    "sample_size": 10,
    "use_mock": true
  }'
```

### Backend Project Structure
```
backend/
├── app/
│   ├── main.py           # FastAPI app
│   ├── core/
│   │   └── config.py     # Configuration
│   ├── routes/
│   │   ├── health.py     # Health endpoints
│   │   ├── surveys.py    # Survey endpoints
│   │   └── websocket.py  # WebSocket endpoint
│   ├── models/
│   │   ├── request.py    # Request models
│   │   └── response.py   # Response models
│   └── services/
│       └── survey.py     # Business logic
├── tests/
│   ├── test_health.py
│   ├── test_surveys.py
│   └── test_models.py
└── requirements.txt
```
