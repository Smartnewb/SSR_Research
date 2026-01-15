# SSR Market Research Tool - Implementation Plan

## Phase 1: Core SSR Engine (MVP) ✅ COMPLETE

### 1. Project Setup ✅
- [x] Create Python project structure (src/, tests/, examples/)
- [x] Set up `requirements.txt` with dependencies
  - openai
  - numpy
  - pandas
  - scikit-learn
  - python-dotenv
  - pytest
  - streamlit (for Phase 2)
- [x] Create `.env.example` with placeholder API keys
- [x] Add `.gitignore` (exclude `.env`, `__pycache__`, `.cache/`)
- [x] Initialize README.md with setup instructions

### 2. SSR Algorithm Implementation ✅
- [x] Implement `src/ssr/utils.py` (cosine_similarity function)
- [x] Implement `src/ssr/anchors.py` (anchor text definitions)
- [x] Implement `src/ssr/calculator.py` (SSRCalculator class)
  - [x] `calculate_simple()` method
  - [x] `calculate_projection()` method (optional)
  - [x] `calculate_batch()` method for efficiency
- [x] Write unit tests for `test_ssr.py` (27 tests)
  - [x] Test cosine similarity math
  - [x] Test score normalization (output in [0, 1])
  - [x] Test with known positive/negative inputs

### 3. Embedding Service ✅
- [x] Implement `src/embeddings/service.py`
  - [x] `get_embedding()` for single text
  - [x] `get_embeddings_batch()` for multiple texts
  - [x] Error handling for API failures
- [x] Implement `src/embeddings/cache.py`
  - [x] File-based caching with pickle
  - [x] Cache key generation (hash of text + model)
- [x] Write unit tests for `test_embeddings.py` (17 tests)
  - [x] Test embedding shape (1536 dims)
  - [x] Test batch processing
  - [x] Test caching behavior

### 4. Persona Generation ✅
- [x] Implement `src/personas/templates.py` (attribute dictionaries)
- [x] Implement `src/personas/generator.py`
  - [x] `generate_persona_hybrid()` function
  - [x] Consistency validation rules
  - [x] `persona_to_system_prompt()` conversion
- [x] Implement `src/personas/validator.py`
  - [x] Age range check (18-80)
  - [x] Coherence warnings
- [x] Write unit tests for `test_personas.py` (29 tests)
  - [x] Test attribute ranges
  - [x] Test system prompt generation
  - [x] Test validation logic

### 5. Survey Execution ✅
- [x] Implement `src/survey/prompts.py` (prompt templates)
- [x] Implement `src/survey/executor.py`
  - [x] `get_purchase_opinion()` function
  - [x] Retry logic with exponential backoff
  - [x] Cost tracking integration
- [x] Implement `src/survey/validator.py`
  - [x] `validate_llm_response()` (detect numeric ratings)
  - [x] Anti-pattern matching (regex)
- [x] Write integration tests for `test_survey.py` (37 tests)
  - [x] Test LLM API call structure
  - [x] Test response validation
  - [x] Test retry logic

### 6. End-to-End Pipeline ✅
- [x] Create `src/pipeline.py` orchestrating all components
  - [x] Input: product description, demographics, sample size
  - [x] Output: list of (persona, response, ssr_score)
- [x] Implement `src/reporting/aggregator.py`
  - [x] Calculate mean, median, std dev
  - [x] Generate score distribution
- [x] Write unit tests for `test_reporting.py` (15 tests)
  - [x] Validate score range (all in [0, 1])

### 7. Example Data & Validation ✅
- [x] Create `examples/product_concepts.json` with 7 test products
  - Positive concept (e.g., "Free coffee every morning")
  - Negative concept (e.g., "$1000 for a plastic cup")
  - Neutral concept (e.g., "New email app")
- [x] Write E2E tests with mock data (`test_pipeline.py` - 10 tests)
- [x] Document expected score ranges in `examples/expected_results.json`

**Total Tests: 160 passing, 1 skipped (requires API key)**

---

## Phase 2: User Interface ✅ COMPLETE

### 8. Streamlit Web App ✅
- [x] Implement `src/ui/app.py` (Streamlit entrypoint)
  - [x] Input form for product description
  - [x] Demographic targeting options
  - [x] Sample size slider (5-200)
- [x] Results dashboard
  - [x] Big number: Average SSR score
  - [x] Histogram: Score distribution
  - [x] Table: Sample responses with quotes
- [x] CSV export functionality
- [x] Cost tracker display (total $ spent)

### 9. CLI Interface ✅
- [x] Create `src/cli.py` using `argparse`
  - [x] `--product` flag for product description
  - [x] `--sample-size` flag
  - [x] `--output` flag for CSV export
- [x] Pretty-print results with `rich` library

---

## Phase 3: Optimization & Polish ✅ COMPLETE

### 10. Performance Optimization ✅
- [x] Add progress bar for long surveys (tqdm/rich)
- [x] Batch embedding requests (already implemented in service.py)
- [ ] Implement parallel LLM calls (async/await) - *optional future enhancement*

### 11. Advanced Features ✅
- [x] A/B testing mode (compare two products side-by-side)
  - Full statistical analysis (t-test, Cohen's d, 95% CI)
  - CLI: `--compare` and `--name-a`/`--name-b` flags
  - Mock mode support for testing
- [ ] Custom anchor texts (user-definable) - *future enhancement*
- [ ] Qualitative analysis (extract themes from responses) - *future enhancement*

### 12. Documentation ✅
- [x] Write `README.md` with:
  - [x] Installation instructions
  - [x] Quick start guide
  - [x] API key setup
  - [x] Example usage
- [x] Create `AGENT.md` with build/run commands
- [x] Add docstrings to all public functions

---

## Project Status: COMPLETE 🎉

All three phases implemented successfully:
- Phase 1: Core SSR Engine ✅
- Phase 2: User Interface ✅
- Phase 3: Optimization & Polish ✅

**Total: 160 tests passing, 1 skipped**

---

## Definition of Done (Exit Criteria)

- [x] All Phase 1 tasks completed
- [x] All tests passing (pytest) - **160 tests passing**
- [ ] Example products generate varied scores (std dev > 0.5) - *requires live API test*
- [ ] Cost per 100 respondents < $1.00 - *requires live API test*
- [ ] Execution time < 2 minutes for N=100 - *requires live API test*
- [x] Code follows Python style guide (PEP 8)
- [x] No hardcoded API keys in code
- [x] README.md has clear setup instructions

---

## Notes
- Use `gpt-5-mini` for cost efficiency (or `gpt-5.2` with reasoning="none")
- Reasoning effort = "none" for fast responses (CRITICAL for speed)
- Verbosity = "medium" for balanced output length
- Batch embeddings to reduce API calls
- Cache anchor embeddings (compute once, reuse)
- Test with mock data before burning API credits
- Use Responses API (not Chat Completions) for GPT-5.2
