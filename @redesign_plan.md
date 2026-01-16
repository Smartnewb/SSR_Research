# SSR Market Research Platform - Redesign Plan

## Problem Statement

현재 구현이 논문의 워크플로우와 맞지 않음. 사용자가 원하는 정확한 프로세스를 따르도록 재설계 필요.

## Correct Workflow (논문 기반)

```
Run Survey 버튼
    ↓
1. Product Description
   - 제품 개요 작성
   - GPT API 작성 보조
    ↓
2. Core Persona Builder (7 fields)
   - Age range
   - Gender distribution
   - Income brackets
   - Location
   - Category usage
   - Shopping behavior
   - Key pain points & decision drivers
   - [Optional] Gemini Research 프롬프트 생성
   - [Optional] 시장조사 결과 첨부 → AI 분석 → 정확한 페르소나
    ↓
3. Confirm Core Persona
   - 최종 확인
    ↓
4. Sample Size Selection
   - 100 / 500 / 1000 / 5000 / 10000 선택
    ↓
5. Generate Persona Variations (백그라운드)
   - Core Persona 기반으로 N개 JSON 생성
   - 분포 통계 맞춤
    ↓
6. Run Survey (WebSocket 진행률)
   - 각 페르소나에게 제품 소개
   - 반응 수집
   - SSR 점수 계산
    ↓
7. Results Dashboard
   - SSR 점수 분포
   - 인구통계별 분석
   - 자유 응답 텍스트
```

## Backend API Redesign

### New Routes Structure

```python
# /api/surveys - Survey workflow orchestration
POST /api/surveys/workflows              # Create new survey workflow
GET  /api/surveys/workflows/{id}         # Get workflow status
POST /api/surveys/workflows/{id}/step    # Progress to next step

# /api/products - Product description
POST /api/products/describe              # AI-assisted product description
POST /api/products                       # Save product description

# /api/personas - Persona management
POST /api/personas/core                  # Save core persona (7 fields)
POST /api/personas/research/prompt       # Generate Gemini research prompt
POST /api/personas/research/parse        # Parse research report → enhance persona
GET  /api/personas/core/{id}             # Get core persona
POST /api/personas/generate              # Generate N variations
GET  /api/personas/generate/{job_id}     # Check generation status

# /api/surveys/{id}/execute - Execute survey
POST /api/surveys/{id}/execute           # Start survey execution
WS   /api/surveys/{id}/progress          # WebSocket for real-time progress
GET  /api/surveys/{id}/results           # Get final results
```

### Models Structure

```python
# Product
class ProductDescription(BaseModel):
    name: str
    category: str
    description: str
    features: list[str]
    price_point: Optional[str]
    target_market: str

# Core Persona (7 fields)
class CorePersona(BaseModel):
    id: str
    age_range: tuple[int, int]              # e.g. (25, 45)
    gender_distribution: dict[str, float]   # {"female": 0.6, "male": 0.4}
    income_brackets: dict[str, float]       # {"low": 0.2, "mid": 0.6, "high": 0.2}
    location: str                           # "urban" / "suburban" / "rural"
    category_usage: str                     # "high" / "medium" / "low"
    shopping_behavior: str                  # "price_sensitive" / "quality_focused" / ...
    key_pain_points: list[str]
    decision_drivers: list[str]

# Survey Workflow
class SurveyWorkflow(BaseModel):
    id: str
    product_id: str
    core_persona_id: str
    sample_size: int
    status: WorkflowStatus  # "product_input" / "persona_building" / "generating" / "surveying" / "completed"
    current_step: int
    created_at: datetime
    completed_at: Optional[datetime]

# Persona Variation
class PersonaVariation(BaseModel):
    id: str
    core_persona_id: str
    age: int
    gender: str
    income: str
    location: str
    category_usage: str
    shopping_behavior: str
    pain_points: list[str]
    decision_drivers: list[str]
    system_prompt: str  # LLM system prompt

# Survey Result
class SurveyResult(BaseModel):
    workflow_id: str
    total_respondents: int
    execution_time: float
    ssr_scores: list[float]
    responses: list[PersonaResponse]
    statistics: SurveyStatistics

class PersonaResponse(BaseModel):
    persona_id: str
    demographics: dict
    response_text: str
    ssr_score: float
    purchase_intent: str  # "very_likely" / "likely" / "neutral" / "unlikely" / "very_unlikely"
```

## Frontend Redesign

### New Pages Structure

```
/surveys/new
  ↓
/surveys/{id}/product        # Step 1: Product Description
  ↓
/surveys/{id}/persona        # Step 2: Core Persona Builder
  - Main Form (7 fields)
  - [Button] Generate Gemini Research Prompt
  - [Upload] Attach Research Report
  ↓
/surveys/{id}/confirm        # Step 3: Confirm Core Persona
  ↓
/surveys/{id}/sample-size    # Step 4: Select Sample Size
  ↓
/surveys/{id}/generating     # Step 5: Generating Personas (Progress)
  ↓
/surveys/{id}/executing      # Step 6: Running Survey (WebSocket)
  ↓
/surveys/{id}/results        # Step 7: Results Dashboard
```

### UI Components

1. **ProductDescriptionForm** (Step 1)
   - Text inputs for product details
   - "Get AI Help" button → GPT suggestions
   - Auto-save draft

2. **CorePersonaForm** (Step 2)
   - 7 structured fields
   - AI assistance for each field
   - "Generate Research Prompt" → modal with Gemini prompt
   - File upload for research report
   - "Parse Research Report" → AI extracts insights

3. **PersonaConfirmation** (Step 3)
   - Read-only view of core persona
   - Edit button → back to step 2
   - "Confirm & Continue"

4. **SampleSizeSelector** (Step 4)
   - Radio buttons: 100 / 500 / 1000 / 5000 / 10000
   - Cost estimate per option
   - Time estimate

5. **GenerationProgress** (Step 5)
   - Progress bar for persona generation
   - Distribution preview (charts)
   - Auto-advance when complete

6. **SurveyExecution** (Step 6)
   - WebSocket connection
   - Real-time progress (X / N completed)
   - Sample responses preview
   - ETA

7. **ResultsDashboard** (Step 7)
   - SSR score distribution (histogram)
   - Demographics breakdown
   - Purchase intent categories
   - Free-text responses table
   - Export CSV/JSON

## Implementation Steps

### Phase 1: Backend Redesign (Week 1-2)
- [ ] Create new route structure
- [ ] Implement workflow state machine
- [ ] Product description API + GPT assistance
- [ ] Core persona API (7 fields)
- [ ] Gemini research prompt generator
- [ ] Research report parser (GPT extraction)
- [ ] Persona variation generator (NumPy distributions)
- [ ] Survey executor with proper SSR calculation
- [ ] WebSocket progress updates

### Phase 2: Frontend Redesign (Week 2-3)
- [ ] Multi-step form wizard
- [ ] Product description page
- [ ] Core persona builder (7 fields)
- [ ] Research assistant integration
- [ ] Sample size selector
- [ ] Generation progress page
- [ ] Survey execution page (WebSocket)
- [ ] Results dashboard

### Phase 3: Integration & Testing (Week 3-4)
- [ ] End-to-end workflow testing
- [ ] Error handling & validation
- [ ] Loading states & UX polish
- [ ] Data persistence (SQLite or in-memory)
- [ ] Export functionality

### Phase 4: Documentation (Week 4)
- [ ] API documentation
- [ ] User guide with screenshots
- [ ] Example workflows

## Key Differences from Current Implementation

| Current | New (Correct) |
|---------|---------------|
| Separate pages for research/concept/survey | Unified workflow with steps |
| Research assistant is optional addon | Research is embedded in persona building |
| Concept builder has unnecessary fields | Core persona follows paper (7 fields) |
| Personas generated separately | Personas generated as part of workflow |
| No product description step | Product description is step 1 |
| No Gemini research integration | Gemini research prompt + report parsing |
| Direct to survey | Multi-step guided process |

## Expected Outcome

사용자가 "Run Survey" 버튼을 누르면:
1. 제품 설명 작성 (GPT 도움)
2. 페르소나 구체화 (논문의 7 필드 폼)
   - Optional: Gemini 리서치 프롬프트 생성
   - Optional: 리서치 결과 첨부 → AI가 페르소나 정확도 향상
3. 페르소나 확정
4. 모수 선택 (100~10000)
5. 페르소나 Variation 자동 생성
6. 설문 실행 (WebSocket 실시간 진행률)
7. 결과 확인

이 모든 과정이 하나의 연결된 워크플로우로 진행됩니다.
