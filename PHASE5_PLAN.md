# Phase 5: Advanced Features Implementation

**시작일**: 2026-01-16
**목표**: Multi-concept comparison 및 고급 분석 기능 추가

---

## 🎯 Phase 5 우선순위

### Priority 1: Multi-Concept Comparison (1주)
**비즈니스 가치**: ⭐⭐⭐⭐⭐ (최고)
**구현 난이도**: 🔧🔧🔧 (중)

**기능 개요**:
- 최대 5개 제품 컨셉을 동시에 테스트
- 동일한 페르소나 세트로 공정한 비교
- 상대적 선호도 분석 (Rank-based comparison)
- 승자/패자 분석 (Winner takes all vs Balanced preference)

**구현 계획**:
1. Backend: `/api/surveys/multi-compare` 엔드포인트
2. Frontend: `/surveys/multi-compare` 페이지
3. 비교 알고리즘: Pairwise comparison + Aggregate scoring
4. 시각화: Radar chart, Bar chart, Heatmap

---

### Priority 2: Price Sensitivity Analysis (3-5일)
**비즈니스 가치**: ⭐⭐⭐⭐ (높음)
**구현 난이도**: 🔧🔧 (낮음-중)

**기능 개요**:
- 동일 컨셉, 여러 가격대 테스트 (예: ₩5,000 / ₩7,000 / ₩9,000)
- Price elasticity curve 생성
- Optimal price point 추천
- Revenue maximization 시뮬레이션

**구현 계획**:
1. Backend: `/api/surveys/price-sensitivity` 엔드포인트
2. Frontend: Price slider + Real-time curve visualization
3. 통계 분석: Demand curve fitting (linear/exponential)
4. 시각화: Line chart, Revenue projection table

---

### Priority 3: Automated Insights Extraction (2-3일)
**비즈니스 가치**: ⭐⭐⭐⭐ (높음)
**구현 난이도**: 🔧🔧 (낮음-중)

**기능 개요**:
- LLM 기반 자동 인사이트 추출
- Open-ended responses 분석 (Qualitative → Quantitative)
- Theme clustering (Key pain points, Decision drivers)
- Executive summary 자동 생성

**구현 계획**:
1. Backend: `/api/analyze/insights` 엔드포인트
2. Claude/GPT-4로 response aggregation
3. Sentiment analysis (Positive/Negative/Neutral)
4. 시각화: Word cloud, Theme frequency bar chart

---

## 📐 Phase 5.1 상세 설계: Multi-Concept Comparison

### User Journey
```
1. User uploads/selects 2-5 product concepts
2. User selects persona set (from previous generation)
3. System runs SSR survey for each concept
4. System calculates:
   - Absolute scores (individual SSR)
   - Relative preference (rank-based)
   - Statistical significance (t-test, ANOVA)
5. Display results:
   - Side-by-side comparison table
   - Radar chart (features comparison)
   - Winner by demographic segment
```

### Backend API Design

#### Endpoint: `POST /api/surveys/multi-compare`

**Request**:
```json
{
  "concepts": [
    {
      "id": "CONCEPT_001",
      "title": "Colgate 3-Day White",
      "headline": "단 3일, 2단계 더 밝은 미소",
      "consumer_insight": "커피로 누렇게 변한 치아...",
      "benefit": "임상 검증된 미백 효과",
      "rtb": "과산화수소 3%",
      "image_description": "빨간 광택 튜브",
      "price": "8,900원 (120g)"
    },
    {
      "id": "CONCEPT_002",
      "title": "Sensodyne ProWhite",
      "headline": "민감하지만 하얗게",
      "consumer_insight": "미백 치약은 잇몸이 시려서...",
      "benefit": "민감성 완화 + 미백 동시에",
      "rtb": "질산칼륨 5% + 미백 실리카",
      "image_description": "파란색 튜브, 보호막 아이콘",
      "price": "12,900원 (120g)"
    }
  ],
  "persona_set_id": "PERSONA_SET_001",
  "sample_size": 500,
  "comparison_mode": "rank_based"  // or "absolute"
}
```

**Response**:
```json
{
  "comparison_id": "CMP_20260116_001",
  "results": {
    "absolute_scores": [
      {
        "concept_id": "CONCEPT_001",
        "mean_ssr": 0.78,
        "std_dev": 0.15,
        "distribution": {
          "definitely_buy": 0.45,
          "probably_buy": 0.32,
          "maybe": 0.18,
          "unlikely": 0.05
        }
      },
      {
        "concept_id": "CONCEPT_002",
        "mean_ssr": 0.72,
        "std_dev": 0.18,
        "distribution": {...}
      }
    ],
    "relative_preference": {
      "winner": "CONCEPT_001",
      "preference_matrix": [
        ["CONCEPT_001", "CONCEPT_002", 0.63],  // 63% prefer 001 over 002
        ["CONCEPT_002", "CONCEPT_001", 0.37]
      ]
    },
    "statistical_significance": {
      "t_statistic": 4.23,
      "p_value": 0.0001,
      "is_significant": true,
      "confidence_level": 0.95
    },
    "segment_analysis": [
      {
        "segment": "age_30_40",
        "winner": "CONCEPT_001",
        "mean_diff": 0.08
      },
      {
        "segment": "high_income",
        "winner": "CONCEPT_002",
        "mean_diff": 0.04
      }
    ],
    "key_differentiators": [
      "Price sensitivity (CONCEPT_001 wins in mid-income)",
      "Sensitivity concerns (CONCEPT_002 wins in high-usage)",
      "Speed of results (CONCEPT_001 '3-day' resonates)"
    ]
  },
  "execution_time_ms": 45000,
  "total_cost_usd": 12.50
}
```

---

### Backend Implementation

#### 1. Models (`backend/app/models/comparison.py`)
```python
from typing import List, Literal
from pydantic import BaseModel, Field

class ConceptInput(BaseModel):
    """Single concept for comparison."""
    id: str
    title: str
    headline: str
    consumer_insight: str
    benefit: str
    rtb: str
    image_description: str
    price: str

class MultiCompareRequest(BaseModel):
    """Request for multi-concept comparison."""
    concepts: List[ConceptInput] = Field(..., min_length=2, max_length=5)
    persona_set_id: str
    sample_size: int = Field(default=500, ge=100, le=10000)
    comparison_mode: Literal["rank_based", "absolute"] = "rank_based"

class AbsoluteScore(BaseModel):
    """Absolute SSR score for a concept."""
    concept_id: str
    mean_ssr: float
    std_dev: float
    distribution: dict[str, float]

class RelativePreference(BaseModel):
    """Relative preference between concepts."""
    winner: str
    preference_matrix: List[List]  # [concept_a, concept_b, pref_rate]

class StatisticalSignificance(BaseModel):
    """Statistical test results."""
    t_statistic: float
    p_value: float
    is_significant: bool
    confidence_level: float

class SegmentAnalysis(BaseModel):
    """Winner by demographic segment."""
    segment: str
    winner: str
    mean_diff: float

class MultiCompareResponse(BaseModel):
    """Response for multi-concept comparison."""
    comparison_id: str
    results: dict
    execution_time_ms: int
    total_cost_usd: float
```

#### 2. Service (`backend/app/services/comparison.py`)
```python
import asyncio
from typing import List
import numpy as np
from scipy import stats

async def run_multi_concept_comparison(
    concepts: List[ConceptInput],
    personas: List[dict],
    comparison_mode: str
) -> dict:
    """
    Run SSR survey for multiple concepts and compare results.
    """
    # 1. Run surveys in parallel
    survey_tasks = [
        run_ssr_survey_for_concept(concept, personas)
        for concept in concepts
    ]
    survey_results = await asyncio.gather(*survey_tasks)

    # 2. Calculate absolute scores
    absolute_scores = [
        calculate_absolute_score(result)
        for result in survey_results
    ]

    # 3. Calculate relative preference (if rank_based)
    if comparison_mode == "rank_based":
        relative_pref = calculate_pairwise_preference(survey_results)
    else:
        relative_pref = None

    # 4. Statistical significance testing
    significance = calculate_statistical_significance(survey_results)

    # 5. Segment analysis
    segment_analysis = analyze_by_segments(survey_results, personas)

    # 6. Extract key differentiators (LLM-based)
    differentiators = await extract_key_differentiators(
        concepts, survey_results
    )

    return {
        "absolute_scores": absolute_scores,
        "relative_preference": relative_pref,
        "statistical_significance": significance,
        "segment_analysis": segment_analysis,
        "key_differentiators": differentiators
    }

def calculate_pairwise_preference(results: List) -> dict:
    """
    Calculate pairwise preference rates.

    For each persona, rank concepts by SSR score.
    Count how many times concept_a beats concept_b.
    """
    n_concepts = len(results)
    preference_matrix = np.zeros((n_concepts, n_concepts))

    for persona_idx in range(len(results[0]["scores"])):
        scores = [
            results[concept_idx]["scores"][persona_idx]
            for concept_idx in range(n_concepts)
        ]
        ranks = np.argsort(scores)[::-1]  # Higher score = better rank

        for i in range(n_concepts):
            for j in range(i + 1, n_concepts):
                if ranks[i] < ranks[j]:  # i ranks better than j
                    preference_matrix[i][j] += 1
                else:
                    preference_matrix[j][i] += 1

    # Normalize to percentages
    n_personas = len(results[0]["scores"])
    preference_matrix /= n_personas

    return {
        "winner": get_winner(preference_matrix),
        "preference_matrix": format_matrix(preference_matrix, results)
    }

def calculate_statistical_significance(results: List) -> dict:
    """
    ANOVA test for multiple concepts.
    If only 2 concepts, use t-test.
    """
    scores = [result["scores"] for result in results]

    if len(scores) == 2:
        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(scores[0], scores[1])
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "is_significant": p_value < 0.05,
            "confidence_level": 0.95
        }
    else:
        # One-way ANOVA
        f_stat, p_value = stats.f_oneway(*scores)
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "is_significant": p_value < 0.05,
            "confidence_level": 0.95
        }

async def extract_key_differentiators(
    concepts: List[ConceptInput],
    results: List
) -> List[str]:
    """
    Use LLM to identify key differentiators between concepts.
    """
    from anthropic import Anthropic

    client = Anthropic()

    # Prepare comparison data
    comparison_text = "\n\n".join([
        f"**Concept {i+1}: {concept.title}**\n"
        f"- Headline: {concept.headline}\n"
        f"- Price: {concept.price}\n"
        f"- Mean SSR: {results[i]['mean_ssr']:.2f}\n"
        f"- Top Positive Theme: {results[i]['top_theme']}"
        for i, concept in enumerate(concepts)
    ])

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Analyze these product concepts and identify 3-5 key differentiators that explain performance differences:

{comparison_text}

Output as a bullet list of key differentiators with brief explanations."""
        }]
    )

    # Parse bullet points
    text = response.content[0].text
    differentiators = [
        line.strip("- ").strip()
        for line in text.split("\n")
        if line.strip().startswith("-")
    ]

    return differentiators[:5]
```

#### 3. Route (`backend/app/routes/comparison.py`)
```python
from fastapi import APIRouter, HTTPException
from backend.app.models.comparison import (
    MultiCompareRequest,
    MultiCompareResponse
)
from backend.app.services.comparison import run_multi_concept_comparison
import time
import uuid

router = APIRouter(prefix="/api/surveys", tags=["comparison"])

@router.post("/multi-compare", response_model=MultiCompareResponse)
async def multi_concept_comparison(request: MultiCompareRequest):
    """
    Compare 2-5 product concepts side-by-side.

    Returns absolute scores, relative preference, statistical significance,
    and segment-level analysis.
    """
    start_time = time.time()

    try:
        # Load persona set
        personas = load_persona_set(request.persona_set_id)

        if len(personas) < request.sample_size:
            raise HTTPException(
                status_code=400,
                detail=f"Persona set has only {len(personas)} personas, "
                       f"but {request.sample_size} requested"
            )

        # Sample personas
        sampled_personas = personas[:request.sample_size]

        # Run comparison
        results = await run_multi_concept_comparison(
            concepts=request.concepts,
            personas=sampled_personas,
            comparison_mode=request.comparison_mode
        )

        execution_time = int((time.time() - start_time) * 1000)

        # Estimate cost (rough: $0.01 per persona per concept)
        total_cost = len(request.concepts) * request.sample_size * 0.01

        return MultiCompareResponse(
            comparison_id=f"CMP_{uuid.uuid4().hex[:12]}",
            results=results,
            execution_time_ms=execution_time,
            total_cost_usd=total_cost
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Frontend Implementation

#### Page: `frontend/src/app/surveys/multi-compare/page.tsx`

**Key Components**:
1. **Concept Upload Panel** - Drag & drop 2-5 concepts
2. **Persona Selector** - Choose from saved persona sets
3. **Comparison Settings** - Sample size, comparison mode
4. **Results Dashboard**:
   - Side-by-side comparison table
   - Radar chart (feature scores)
   - Preference heatmap
   - Statistical significance badge
   - Segment analysis cards
   - Key differentiators list

**Sample Code**:
```tsx
'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadarChart, BarChart } from '@/components/charts';

export default function MultiComparePage() {
  const [concepts, setConcepts] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRunComparison = async () => {
    setLoading(true);

    const response = await fetch('/api/surveys/multi-compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        concepts,
        persona_set_id: selectedPersonaSet,
        sample_size: 500,
        comparison_mode: 'rank_based'
      })
    });

    const data = await response.json();
    setResults(data.results);
    setLoading(false);
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Multi-Concept Comparison</h1>

      {/* Concept Upload */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Upload Concepts (2-5)</CardTitle>
        </CardHeader>
        <CardContent>
          <ConceptUploader
            concepts={concepts}
            onChange={setConcepts}
            maxConcepts={5}
          />
        </CardContent>
      </Card>

      {/* Run Comparison */}
      <Button
        onClick={handleRunComparison}
        disabled={concepts.length < 2 || loading}
        size="lg"
      >
        {loading ? 'Running Comparison...' : 'Compare Concepts'}
      </Button>

      {/* Results */}
      {results && (
        <div className="mt-8 space-y-8">
          {/* Absolute Scores */}
          <Card>
            <CardHeader>
              <CardTitle>📊 Absolute Scores</CardTitle>
            </CardHeader>
            <CardContent>
              <BarChart data={results.absolute_scores} />
            </CardContent>
          </Card>

          {/* Radar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>🎯 Feature Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <RadarChart data={results.radar_data} />
            </CardContent>
          </Card>

          {/* Key Differentiators */}
          <Card>
            <CardHeader>
              <CardTitle>🔑 Key Differentiators</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-6 space-y-2">
                {results.key_differentiators.map((diff, i) => (
                  <li key={i}>{diff}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
```

---

## 📅 구현 일정

### Week 1: Multi-Concept Comparison
- Day 1-2: Backend API + Models
- Day 3-4: Frontend UI + Charts
- Day 5: Testing + Bug fixes
- Day 6-7: Documentation + Polish

### Week 2: Price Sensitivity (Optional)
- Day 1-2: Backend implementation
- Day 3-4: Frontend slider + curve visualization
- Day 5: Integration testing

---

## ✅ Definition of Done (Phase 5.1)

- [ ] Backend `/api/surveys/multi-compare` endpoint working
- [ ] Statistical significance calculation (t-test/ANOVA)
- [ ] Segment analysis by demographics
- [ ] LLM-based key differentiators extraction
- [ ] Frontend multi-compare page functional
- [ ] Radar chart + Bar chart visualization
- [ ] 10+ backend tests for comparison logic
- [ ] End-to-end test: 3 concepts, 500 personas
- [ ] Documentation updated

---

**시작 준비 완료. 구현을 시작하겠습니다!** 🚀
