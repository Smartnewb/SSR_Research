# Synthetic Market Research Tool - Development Instructions

## Project Overview
This project implements a **Semantic Similarity Rating (SSR)** based market research tool that generates synthetic consumer purchase intent data using LLMs. Based on the methodology from *"LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings"* (Maier et al., 2025, arXiv:2510.08338).

## Core Innovation
Instead of asking LLMs for direct numerical ratings (which causes central tendency bias), we:
1. Generate synthetic personas with demographic profiles
2. Elicit free-text opinions about products
3. Calculate purchase intent via cosine similarity between responses and semantic anchors
4. Achieve >0.9 correlation with human behavior

## Target Users
- Product Managers conducting rapid concept testing
- Solo Developers validating product-market fit
- Researchers exploring synthetic data methods

## Success Criteria
- **Variance**: Produce diverse scores (not bunched around middle)
- **Cost**: <$1 per 100 synthetic respondents
- **Speed**: Results in <2 minutes
- **Correlation**: Match human intent patterns

## Development Phases

### Phase 1: Core SSR Engine (MVP)
1. Implement SSR calculation algorithm
2. Create persona generation system
3. Build LLM integration for free-text responses
4. Validate math with hardcoded test cases

### Phase 2: User Interface
1. Streamlit web UI for product concept input
2. Results dashboard with visualizations
3. CSV export functionality
4. A/B testing comparison mode

### Phase 3: Optimization
1. Fine-tune anchor texts for better sensitivity
2. Experiment with different embedding models
3. Add qualitative analysis (theme extraction)
4. Cost/performance optimization

## Technical Stack
- **Language**: Python 3.9+
- **LLM**: OpenAI GPT-5.2 (or gpt-5-mini for cost optimization)
- **API**: Responses API (with reasoning effort control)
- **Embeddings**: OpenAI text-embedding-3-small
- **Data**: Pandas, NumPy, Scikit-learn
- **UI**: Streamlit
- **Testing**: pytest

## Key Principles
- **No over-engineering**: Build only what's specified
- **Variance is critical**: Avoid central tendency bias
- **Cost-conscious**: Use mini models where possible
- **Reproducible**: Fix random seeds for testing
- **Transparent**: Log all API calls and costs

## Current Objectives
1. Review [specs/](specs/) for detailed technical specifications
2. Implement components in priority order from [@fix_plan.md](fix_plan.md)
3. Write tests for each module as you build
4. Document API usage and costs
5. Validate SSR scores match expected distributions

## File Structure
```
my-project/
├── specs/              # Detailed specifications
│   ├── architecture.md
│   ├── ssr-algorithm.md
│   ├── persona-generation.md
│   └── api-design.md
├── src/
│   ├── ssr/           # Core SSR engine
│   ├── personas/      # Persona generation
│   ├── embeddings/    # Embedding utilities
│   └── ui/            # Streamlit interface
├── tests/             # pytest test suite
├── examples/          # Example product concepts
└── @fix_plan.md       # Prioritized tasks
```

## Testing Strategy
- Unit tests for SSR math (cosine similarity, projection)
- Integration tests for LLM API calls (with mocks)
- End-to-end tests with known product concepts
- Validate variance in output scores
- Check cost per 100 respondents

## Quality Gates
- [ ] SSR algorithm produces scores 0-1 (or 1-5)
- [ ] Free-text responses never contain numbers
- [ ] Scores show variance (std dev > 0.5)
- [ ] Similar products get similar scores
- [ ] Cost tracking works correctly
- [ ] UI is intuitive for non-technical users

## References
- Paper: [arXiv:2510.08338](https://arxiv.org/html/2510.08338v3)
- OpenAI Embeddings: [docs](https://platform.openai.com/docs/guides/embeddings)
- Streamlit: [docs](https://docs.streamlit.io/)

---

**Start by reading [specs/architecture.md](specs/architecture.md) to understand the system design.**
