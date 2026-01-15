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

---

## Phase 4: Modern Web Interface 🚀 IN PROGRESS

### 13. Technology Stack Selection ✅
**Goal**: Replace Streamlit with a modern, production-ready web stack

#### Frontend Framework Options
- [x] **Next.js + React** (Selected)
  - TypeScript for type safety
  - Server-side rendering (SSR) for SEO
  - API routes for backend integration
  - Tailwind CSS for styling
  - shadcn/ui for component library

**Decision**: Next.js + React (most mature ecosystem, better for complex UIs)

---

### 14. Backend API Development ✅ COMPLETE
**Goal**: Create RESTful API to replace direct Python execution

#### 14.1 API Architecture ✅
- [x] Design RESTful API endpoints
  - `POST /api/surveys` - Run survey
  - `POST /api/surveys/compare` - A/B testing
  - `GET /api/surveys/:id/export` - Download CSV (placeholder)
  - `GET /health` - Health check

#### 14.2 Framework Selection ✅
- [x] **FastAPI** (Selected)
  - Modern Python async framework
  - Auto-generated OpenAPI docs
  - Type hints with Pydantic
  - WebSocket support for real-time updates

#### 14.3 Implementation Tasks ✅
- [x] Set up FastAPI project structure
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py           # FastAPI app
  │   ├── routes/
  │   │   ├── surveys.py    # Survey endpoints
  │   │   ├── health.py     # Health check
  │   │   └── websocket.py  # WebSocket endpoint
  │   ├── models/
  │   │   ├── request.py    # Pydantic request models
  │   │   └── response.py   # Pydantic response models
  │   ├── services/
  │   │   └── survey.py     # Business logic
  │   └── core/
  │       └── config.py     # Configuration
  ├── requirements.txt
  └── tests/
  ```

- [x] Implement core endpoints
  - [x] `POST /api/surveys` - Run survey with progress tracking
  - [x] `POST /api/surveys/compare` - A/B testing

- [x] Add WebSocket support for real-time progress
  - [x] `/ws/surveys/:id` - Live progress updates
  - [x] Send progress percentage, current persona, estimated time

- [x] Add request validation
  - [x] Pydantic models for all requests
  - [x] Input sanitization
  - [ ] Rate limiting - *future enhancement*

- [x] Add error handling
  - [x] Custom error responses
  - [x] Survey execution errors
  - [x] Proper HTTP status codes

- [x] Add CORS configuration
  - [x] Allow frontend origin (localhost:3000)
  - [x] Secure credentials handling

- [x] Write API tests
  - [x] Unit tests for each endpoint (21 tests passing)
  - [x] Integration tests with mock data
  - [ ] Load testing for concurrent surveys - *future enhancement*

---

### 15. Frontend Development (Next.js + React)
**Goal**: Build modern, responsive web UI

#### 15.1 Project Setup
- [ ] Initialize Next.js project with TypeScript
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --app
  ```
- [ ] Install dependencies
  - [ ] `@tanstack/react-query` - Server state management
  - [ ] `axios` - HTTP client
  - [ ] `recharts` - Charts and visualizations
  - [ ] `shadcn/ui` - Component library
  - [ ] `zustand` - Client state management
  - [ ] `react-hook-form` - Form handling
  - [ ] `zod` - Schema validation

#### 15.2 Project Structure
```
frontend/
├── app/
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── surveys/
│   │   ├── new/
│   │   │   └── page.tsx   # Create survey
│   │   ├── [id]/
│   │   │   ├── page.tsx   # Survey results
│   │   │   └── compare/
│   │   │       └── page.tsx # A/B testing
│   └── api/               # Next.js API routes (proxy)
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── survey/
│   │   ├── SurveyForm.tsx
│   │   ├── ResultsDashboard.tsx
│   │   ├── ScoreDistribution.tsx
│   │   ├── PersonaTable.tsx
│   │   └── ProgressTracker.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Footer.tsx
├── lib/
│   ├── api.ts            # API client
│   ├── types.ts          # TypeScript types
│   └── utils.ts          # Utilities
├── hooks/
│   ├── useSurvey.ts      # Survey operations
│   └── useWebSocket.ts   # Real-time updates
└── public/
    └── assets/
```

#### 15.3 Page Development

##### 15.3.1 Home Page (`/`)
- [ ] Hero section
  - [ ] Project title and description
  - [ ] "Start Survey" CTA button
  - [ ] Key features showcase

- [ ] Features section
  - [ ] SSR methodology explanation
  - [ ] Cost comparison table
  - [ ] Speed comparison

- [ ] Getting started guide
  - [ ] Quick tutorial
  - [ ] Example results preview

##### 15.3.2 Create Survey Page (`/surveys/new`)
- [ ] Product input form
  - [ ] Product description textarea
  - [ ] Character count indicator
  - [ ] Example products dropdown

- [ ] Demographics configuration
  - [ ] Age range slider (18-80)
  - [ ] Gender selection (checkboxes)
  - [ ] Occupation multi-select
  - [ ] Income bracket selection
  - [ ] Location selection

- [ ] Survey settings
  - [ ] Sample size slider (5-200)
  - [ ] Mock mode toggle
  - [ ] SSR method selection (simple/projection)

- [ ] Cost estimator
  - [ ] Real-time cost calculation
  - [ ] Token usage estimate
  - [ ] Execution time estimate

- [ ] Form validation
  - [ ] Required field checks
  - [ ] Input sanitization
  - [ ] Error messages

##### 15.3.3 Survey Results Page (`/surveys/[id]`)
- [ ] Results header
  - [ ] Survey ID and timestamp
  - [ ] Product description
  - [ ] Re-run button

- [ ] Key metrics cards
  - [ ] Average SSR score (large number)
  - [ ] Standard deviation
  - [ ] Min/Max scores
  - [ ] Total cost
  - [ ] Execution time

- [ ] Score distribution chart
  - [ ] Histogram with 10 bins
  - [ ] Interactive tooltips
  - [ ] Color coding (red/yellow/green)

- [ ] Persona responses table
  - [ ] Sortable columns (score, age, occupation)
  - [ ] Filterable by demographics
  - [ ] Expandable response text
  - [ ] Pagination (20 per page)

- [ ] Export options
  - [ ] CSV download button
  - [ ] JSON download button
  - [ ] Share results link

- [ ] Insights section
  - [ ] Demographic breakdown
  - [ ] Top positive/negative quotes
  - [ ] Variance analysis

##### 15.3.4 A/B Testing Page (`/surveys/compare`)
- [ ] Product comparison form
  - [ ] Product A input
  - [ ] Product B input
  - [ ] Shared demographics settings
  - [ ] Sample size (per product)

- [ ] Comparison results
  - [ ] Side-by-side score cards
  - [ ] Overlapping distribution charts
  - [ ] Statistical significance (p-value)
  - [ ] Cohen's d effect size
  - [ ] 95% confidence intervals
  - [ ] Winner declaration

- [ ] Detailed breakdown
  - [ ] Score difference by demographic
  - [ ] Response comparison table
  - [ ] Export comparison report

#### 15.4 Component Development

##### 15.4.1 Survey Form Component
- [ ] Product description input with validation
- [ ] Demographics selector (multi-select dropdowns)
- [ ] Sample size slider with visual feedback
- [ ] Mock mode toggle
- [ ] Submit button with loading state
- [ ] Form state management (react-hook-form)

##### 15.4.2 Progress Tracker Component
- [ ] Real-time progress bar
- [ ] WebSocket connection for live updates
- [ ] Current persona display
- [ ] Estimated time remaining
- [ ] Cancel survey button
- [ ] Error state handling

##### 15.4.3 Results Dashboard Component
- [ ] Metric cards with animations
- [ ] Score distribution chart (recharts)
- [ ] Responsive layout (grid)
- [ ] Loading skeletons
- [ ] Empty state handling

##### 15.4.4 Persona Table Component
- [ ] Sortable, filterable data table
- [ ] Expandable rows for full responses
- [ ] Demographic tag pills
- [ ] Copy response to clipboard
- [ ] Highlight feature

##### 15.4.5 Score Distribution Chart
- [ ] Histogram visualization
- [ ] Interactive tooltips
- [ ] Color-coded bins
- [ ] Responsive sizing
- [ ] Export as image

---

### 16. Real-time Features
**Goal**: Provide live feedback during survey execution

#### 16.1 WebSocket Implementation
- [ ] Backend: FastAPI WebSocket endpoint
  - [ ] Connection management
  - [ ] Progress broadcasting
  - [ ] Error handling

- [ ] Frontend: WebSocket hook
  - [ ] Auto-reconnect logic
  - [ ] Message handling
  - [ ] State updates

#### 16.2 Progress Updates
- [ ] Send progress events
  - [ ] Persona generation progress
  - [ ] Survey execution progress (per persona)
  - [ ] Embedding calculation progress
  - [ ] SSR calculation progress

- [ ] Display progress
  - [ ] Progress bar (0-100%)
  - [ ] Current step indicator
  - [ ] Estimated time remaining
  - [ ] Cancel button (graceful shutdown)

---

### 17. Deployment & DevOps
**Goal**: Deploy to production

#### 17.1 Backend Deployment
- [ ] Containerization
  - [ ] Create Dockerfile for FastAPI
  - [ ] Docker Compose for local development
  - [ ] Environment variable management

- [ ] Hosting options
  - [ ] **Option A: Railway** - Simple Python deployment
  - [ ] **Option B: Render** - Free tier available
  - [ ] **Option C: AWS Lambda** - Serverless (complex for long tasks)
  - [ ] **Option D: DigitalOcean App Platform**

**Decision**: Railway (easy Python deployment, good for FastAPI)

#### 17.2 Frontend Deployment
- [ ] Build optimization
  - [ ] Next.js static export or SSR
  - [ ] Image optimization
  - [ ] Code splitting

- [ ] Hosting options
  - [ ] **Vercel** - Best for Next.js (Recommended)
  - [ ] **Netlify** - Alternative
  - [ ] **Cloudflare Pages**

**Decision**: Vercel (native Next.js support)

#### 17.3 Database (Optional)
- [ ] Survey history storage
  - [ ] PostgreSQL for survey results
  - [ ] Redis for caching

- [ ] Hosting
  - [ ] Supabase (PostgreSQL + Auth)
  - [ ] Railway PostgreSQL
  - [ ] Upstash (Redis)

#### 17.4 CI/CD Pipeline
- [ ] GitHub Actions
  - [ ] Run tests on PR
  - [ ] Auto-deploy to staging
  - [ ] Auto-deploy to production (on main merge)

- [ ] Environment management
  - [ ] Development
  - [ ] Staging
  - [ ] Production

---

### 18. Testing Strategy
**Goal**: Ensure web UI quality

#### 18.1 Backend Tests
- [ ] Unit tests (pytest)
  - [ ] API endpoint tests
  - [ ] Request validation tests
  - [ ] Error handling tests

- [ ] Integration tests
  - [ ] End-to-end survey execution
  - [ ] WebSocket communication
  - [ ] Mock mode verification

- [ ] Load tests
  - [ ] Concurrent survey handling
  - [ ] Rate limiting verification

#### 18.2 Frontend Tests
- [ ] Unit tests (Jest + React Testing Library)
  - [ ] Component rendering tests
  - [ ] User interaction tests
  - [ ] Form validation tests

- [ ] E2E tests (Playwright)
  - [ ] Full survey workflow
  - [ ] A/B testing workflow
  - [ ] Export functionality

- [ ] Visual regression tests
  - [ ] Component snapshots
  - [ ] Page screenshots

---

### 19. Documentation
**Goal**: Document new web interface

- [ ] Update README.md
  - [ ] Web UI setup instructions
  - [ ] API documentation link
  - [ ] Deployment guide

- [ ] Create API documentation
  - [ ] OpenAPI/Swagger docs (auto-generated)
  - [ ] Endpoint descriptions
  - [ ] Request/response examples

- [ ] Create user guide
  - [ ] How to run surveys
  - [ ] How to interpret results
  - [ ] A/B testing guide
  - [ ] Troubleshooting

- [ ] Developer guide
  - [ ] Local development setup
  - [ ] Architecture overview
  - [ ] Contributing guidelines

---

## Phase 4 Milestones

### Milestone 1: Backend API (Week 1-2)
- [ ] FastAPI setup complete
- [ ] Core endpoints implemented
- [ ] WebSocket support
- [ ] Tests passing
- [ ] Deployed to Railway

### Milestone 2: Frontend MVP (Week 3-4)
- [ ] Next.js project setup
- [ ] Survey form page
- [ ] Results page (basic)
- [ ] API integration
- [ ] Deployed to Vercel

### Milestone 3: Full Features (Week 5-6)
- [ ] A/B testing page
- [ ] Real-time progress
- [ ] Advanced visualizations
- [ ] Export functionality
- [ ] Mobile responsive

### Milestone 4: Production Ready (Week 7-8)
- [ ] Full test coverage
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation complete
- [ ] User feedback incorporated

---

## Phase 4 Tech Stack Summary

**Backend**:
- FastAPI (Python async web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)
- WebSockets (real-time communication)
- Railway (hosting)

**Frontend**:
- Next.js 14 (React framework with App Router)
- TypeScript (type safety)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- Recharts (data visualization)
- React Query (server state)
- Zustand (client state)
- Vercel (hosting)

**DevOps**:
- Docker (containerization)
- GitHub Actions (CI/CD)
- Vercel + Railway (deployment)

**Optional**:
- Supabase (PostgreSQL + Auth)
- Redis (caching)
- Sentry (error tracking)
