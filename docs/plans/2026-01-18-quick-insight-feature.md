# QuickInsight 기능 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 무료 설문 결과에 경량 인사이트 (한 줄 요약 + Pain Points 3개) 추가하여 유료 전환 유도

**Architecture:** 기존 QIE Tier1 태깅 로직을 재사용하여 전체 응답을 분석하고, 경량 요약 프롬프트로 한 줄 인사이트와 Pain Points 3개를 생성. 설문 실행 완료 시 자동으로 함께 실행.

**Tech Stack:** Python (FastAPI, Pydantic, OpenAI), TypeScript (Next.js, React)

---

## Task 1: Backend 데이터 모델 추가

**Files:**
- Modify: `backend/app/models/response.py:1-137`

**Step 1: PainPointPreview 모델 추가**

`backend/app/models/response.py` 파일 끝에 추가:

```python
class PainPointPreview(BaseModel):
    """무료 결과용 Pain Point 미리보기."""

    rank: int = Field(..., ge=1, le=3)
    title: str = Field(..., max_length=50)
    category: str  # Price, UX, Trust, Feature, Convenience
    is_unlocked: bool = False
    description: Optional[str] = None
    affected_percentage: Optional[float] = Field(None, ge=0, le=100)


class QuickInsight(BaseModel):
    """무료 결과용 경량 인사이트."""

    one_liner: str = Field(..., max_length=200)
    pain_points: list[PainPointPreview] = Field(..., min_length=1, max_length=3)
    generated_at: datetime = Field(default_factory=datetime.now)
```

**Step 2: SurveyResponse에 quick_insight 필드 추가**

`SurveyResponse` 클래스에 필드 추가:

```python
class SurveyResponse(BaseModel):
    """Response model for survey results."""

    survey_id: str
    product_description: str
    sample_size: int
    mean_score: float
    median_score: float
    std_dev: float
    min_score: float
    max_score: float
    score_distribution: dict[str, int]
    total_cost: float
    total_tokens: int
    execution_time_seconds: float
    results: list[SurveyResultItem]
    quick_insight: Optional[QuickInsight] = None  # NEW
    created_at: datetime = Field(default_factory=datetime.now)
```

**Step 3: 변경 사항 확인**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project && python -c "from backend.app.models.response import QuickInsight, PainPointPreview, SurveyResponse; print('Models OK')"`

Expected: `Models OK`

**Step 4: Commit**

```bash
git add backend/app/models/response.py
git commit -m "feat(models): add QuickInsight and PainPointPreview models for free tier insights"
```

---

## Task 2: Tier1 태깅 로직 분리

**Files:**
- Create: `src/insights/__init__.py`
- Create: `src/insights/tier1_tagger.py`
- Reference: `backend/app/services/qie_pipeline.py:39-48` (TIER1_SYSTEM_PROMPT)

**Step 1: insights 패키지 생성**

```python
# src/insights/__init__.py
"""Insights generation package for survey analysis."""

from .tier1_tagger import Tier1Tagger, Tier1TagResult

__all__ = ["Tier1Tagger", "Tier1TagResult"]
```

**Step 2: Tier1Tagger 클래스 작성**

```python
# src/insights/tier1_tagger.py
"""Tier1 response tagging using gpt-5-mini."""

import asyncio
import json
from dataclasses import dataclass
from typing import Optional

import openai


TIER1_SYSTEM_PROMPT = """You are a precise data labeler for market research analysis.

For the given survey response, extract:
1. sentiment: Integer 1-10 (1=very negative, 10=very positive purchase intent)
2. category: ONE of [Price, UX, Trust, Feature, Convenience, Other]
3. keywords: Maximum 5 key words/phrases from the response

Output ONLY valid JSON, no explanation:
{"sentiment": 7, "category": "Price", "keywords": ["affordable", "value"]}"""


@dataclass
class Tier1TagResult:
    """Result from Tier1 tagging of a single response."""

    response_id: str
    sentiment: int  # 1-10
    category: str  # Price, UX, Trust, Feature, Convenience, Other
    keywords: list[str]
    original_text: str
    ssr_score: float


class Tier1Tagger:
    """Tier1 tagger using gpt-5-mini for response labeling."""

    def __init__(
        self,
        model: str = "gpt-5-mini",
        max_concurrent: int = 20,
    ):
        self.model = model
        self.max_concurrent = max_concurrent
        self.client = openai.AsyncOpenAI()
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def tag_single(
        self,
        response_id: str,
        response_text: str,
        ssr_score: float,
    ) -> Tier1TagResult:
        """Tag a single response with sentiment, category, and keywords."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        async with self._semaphore:
            try:
                completion = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": TIER1_SYSTEM_PROMPT},
                        {"role": "user", "content": response_text},
                    ],
                    temperature=0,
                    max_tokens=150,
                )

                content = completion.choices[0].message.content or "{}"
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()

                data = json.loads(content)

                return Tier1TagResult(
                    response_id=response_id,
                    sentiment=int(data.get("sentiment", 5)),
                    category=data.get("category", "Other"),
                    keywords=data.get("keywords", [])[:5],
                    original_text=response_text,
                    ssr_score=ssr_score,
                )

            except (json.JSONDecodeError, KeyError, ValueError):
                # Fallback on parse error
                return Tier1TagResult(
                    response_id=response_id,
                    sentiment=5,
                    category="Other",
                    keywords=[],
                    original_text=response_text,
                    ssr_score=ssr_score,
                )

    async def tag_batch(
        self,
        responses: list[dict],
    ) -> list[Tier1TagResult]:
        """Tag multiple responses in parallel.

        Args:
            responses: List of dicts with keys: persona_id, response_text, ssr_score

        Returns:
            List of Tier1TagResult
        """
        tasks = [
            self.tag_single(
                response_id=r.get("persona_id", f"r_{i}"),
                response_text=r["response_text"],
                ssr_score=r.get("ssr_score", 0.5),
            )
            for i, r in enumerate(responses)
        ]
        return await asyncio.gather(*tasks)
```

**Step 3: 모듈 import 확인**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project && python -c "from src.insights import Tier1Tagger, Tier1TagResult; print('Tier1Tagger OK')"`

Expected: `Tier1Tagger OK`

**Step 4: Commit**

```bash
git add src/insights/
git commit -m "feat(insights): extract Tier1Tagger as reusable module"
```

---

## Task 3: QuickAnalyzer 구현

**Files:**
- Create: `src/insights/quick_analyzer.py`
- Modify: `src/insights/__init__.py`

**Step 1: QuickAnalyzer 클래스 작성**

```python
# src/insights/quick_analyzer.py
"""Quick insight analyzer for free tier survey results."""

import asyncio
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import openai

from .tier1_tagger import Tier1Tagger, Tier1TagResult


QUICK_SUMMARY_PROMPT = """You are a market research analyst. Based on the aggregated survey data below,
provide a BRIEF insight for a free preview.

## Survey Statistics
- Total responses: {total}
- Average SSR score: {mean:.2f} (0-1 scale, 1=high purchase intent)
- Category distribution: {category_dist}
- Top keywords in low-SSR responses (SSR < 0.4): {low_ssr_keywords}
- Top keywords in high-SSR responses (SSR > 0.7): {high_ssr_keywords}

## Your Task
Generate JSON with:
1. one_liner: 1-2 sentence summary of key finding (in Korean, max 150 chars)
2. pain_points: Top 3 purchase barriers, each with:
   - title: Short title (Korean, max 20 chars)
   - category: Price/UX/Trust/Feature/Convenience
   - description: 2-3 sentences explaining the issue (Korean)
   - affected_percentage: estimated % of responses mentioning this issue

Output ONLY valid JSON:
{{
  "one_liner": "...",
  "pain_points": [
    {{"title": "...", "category": "...", "description": "...", "affected_percentage": 45.2}},
    {{"title": "...", "category": "...", "description": "...", "affected_percentage": 30.1}},
    {{"title": "...", "category": "...", "description": "...", "affected_percentage": 15.5}}
  ]
}}

IMPORTANT:
- Be concise - this is a FREE preview, not full analysis
- Focus on problems, not solutions (solutions are in paid tier)
- Korean language for all text fields
- Return exactly 3 pain_points sorted by affected_percentage descending"""


@dataclass
class PainPointData:
    """Pain point data from analysis."""

    rank: int
    title: str
    category: str
    description: str
    affected_percentage: float


@dataclass
class QuickInsightData:
    """Quick insight analysis result."""

    one_liner: str
    pain_points: list[PainPointData]
    generated_at: datetime


class QuickAnalyzer:
    """Analyzer for generating free-tier quick insights."""

    def __init__(
        self,
        tier1_model: str = "gpt-5-mini",
        summary_model: str = "gpt-5-mini",
        max_concurrent: int = 20,
    ):
        self.tagger = Tier1Tagger(model=tier1_model, max_concurrent=max_concurrent)
        self.summary_model = summary_model
        self.client = openai.AsyncOpenAI()

    async def analyze(
        self,
        responses: list[dict],
        mean_score: float,
    ) -> QuickInsightData:
        """Generate quick insights from survey responses.

        Args:
            responses: List of dicts with persona_id, response_text, ssr_score
            mean_score: Mean SSR score of the survey

        Returns:
            QuickInsightData with one_liner and pain_points
        """
        # Step 1: Tag all responses
        tagged_results = await self.tagger.tag_batch(responses)

        # Step 2: Aggregate statistics
        stats = self._aggregate_stats(tagged_results)

        # Step 3: Generate summary
        insight = await self._generate_summary(stats, mean_score, len(responses))

        return insight

    def _aggregate_stats(
        self,
        results: list[Tier1TagResult],
    ) -> dict:
        """Aggregate Tier1 results into statistics."""
        category_counts: Counter = Counter()
        low_ssr_keywords: Counter = Counter()
        high_ssr_keywords: Counter = Counter()

        for r in results:
            category_counts[r.category] += 1

            if r.ssr_score < 0.4:
                low_ssr_keywords.update(r.keywords)
            elif r.ssr_score > 0.7:
                high_ssr_keywords.update(r.keywords)

        total = len(results)
        category_dist = {
            cat: f"{count} ({count/total*100:.1f}%)"
            for cat, count in category_counts.most_common()
        }

        return {
            "category_dist": category_dist,
            "low_ssr_keywords": [kw for kw, _ in low_ssr_keywords.most_common(10)],
            "high_ssr_keywords": [kw for kw, _ in high_ssr_keywords.most_common(10)],
        }

    async def _generate_summary(
        self,
        stats: dict,
        mean_score: float,
        total: int,
    ) -> QuickInsightData:
        """Generate one-liner and pain points using LLM."""
        prompt = QUICK_SUMMARY_PROMPT.format(
            total=total,
            mean=mean_score,
            category_dist=stats["category_dist"],
            low_ssr_keywords=", ".join(stats["low_ssr_keywords"][:10]) or "없음",
            high_ssr_keywords=", ".join(stats["high_ssr_keywords"][:10]) or "없음",
        )

        try:
            completion = await self.client.chat.completions.create(
                model=self.summary_model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            content = completion.choices[0].message.content or "{}"
            # Remove markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            data = json.loads(content)

            pain_points = []
            for i, pp in enumerate(data.get("pain_points", [])[:3], start=1):
                pain_points.append(PainPointData(
                    rank=i,
                    title=pp.get("title", f"문제점 {i}")[:50],
                    category=pp.get("category", "Other"),
                    description=pp.get("description", ""),
                    affected_percentage=float(pp.get("affected_percentage", 0)),
                ))

            return QuickInsightData(
                one_liner=data.get("one_liner", "분석 결과를 확인하세요.")[:200],
                pain_points=pain_points,
                generated_at=datetime.now(),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback
            return QuickInsightData(
                one_liner="설문 분석이 완료되었습니다. 상세 내용은 AI 심층 분석을 이용해주세요.",
                pain_points=[
                    PainPointData(
                        rank=1,
                        title="분석 필요",
                        category="Other",
                        description="AI 심층 분석을 통해 상세한 인사이트를 확인하세요.",
                        affected_percentage=0,
                    )
                ],
                generated_at=datetime.now(),
            )
```

**Step 2: __init__.py 업데이트**

```python
# src/insights/__init__.py
"""Insights generation package for survey analysis."""

from .tier1_tagger import Tier1Tagger, Tier1TagResult
from .quick_analyzer import QuickAnalyzer, QuickInsightData, PainPointData

__all__ = [
    "Tier1Tagger",
    "Tier1TagResult",
    "QuickAnalyzer",
    "QuickInsightData",
    "PainPointData",
]
```

**Step 3: 모듈 import 확인**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project && python -c "from src.insights import QuickAnalyzer, QuickInsightData; print('QuickAnalyzer OK')"`

Expected: `QuickAnalyzer OK`

**Step 4: Commit**

```bash
git add src/insights/
git commit -m "feat(insights): add QuickAnalyzer for free tier insight generation"
```

---

## Task 4: SurveyService에 QuickInsight 통합

**Files:**
- Modify: `backend/app/services/survey.py:1-178`

**Step 1: import 추가**

파일 상단에 import 추가:

```python
import asyncio
from src.insights import QuickAnalyzer, QuickInsightData
from ..models.response import QuickInsight, PainPointPreview
```

**Step 2: _convert_quick_insight 헬퍼 함수 추가**

SurveyService 클래스 내부에 헬퍼 메서드 추가:

```python
def _convert_quick_insight(self, data: QuickInsightData) -> QuickInsight:
    """Convert QuickInsightData to API response model."""
    pain_points = []
    for i, pp in enumerate(data.pain_points):
        pain_points.append(PainPointPreview(
            rank=pp.rank,
            title=pp.title,
            category=pp.category,
            is_unlocked=(i == 0),  # Only first one is unlocked
            description=pp.description if i == 0 else None,
            affected_percentage=pp.affected_percentage if i == 0 else None,
        ))

    return QuickInsight(
        one_liner=data.one_liner,
        pain_points=pain_points,
        generated_at=data.generated_at,
    )
```

**Step 3: run_survey 메서드 수정**

`run_survey` 메서드 끝 부분, `return SurveyResponse(...)` 전에 QuickInsight 생성 추가:

```python
def run_survey(
    self,
    request: SurveyRequest,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> SurveyResponse:
    """Run a survey and return results."""
    survey_id = f"survey_{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    # ... (existing code for demographics and running survey) ...

    execution_time = time.time() - start_time

    result_items = [
        # ... (existing code) ...
    ]

    # NEW: Generate quick insight
    quick_insight = None
    if not request.use_mock and len(result_items) >= 10:
        try:
            responses_for_analysis = [
                {
                    "persona_id": r.persona_id,
                    "response_text": r.response_text,
                    "ssr_score": r.ssr_score,
                }
                for r in result_items
            ]
            analyzer = QuickAnalyzer()
            insight_data = asyncio.run(
                analyzer.analyze(responses_for_analysis, results.mean_score)
            )
            quick_insight = self._convert_quick_insight(insight_data)
        except Exception as e:
            # Log but don't fail the survey
            print(f"QuickInsight generation failed: {e}")
            quick_insight = None

    return SurveyResponse(
        survey_id=survey_id,
        product_description=request.product_description,
        sample_size=results.sample_size,
        mean_score=results.mean_score,
        median_score=results.median_score,
        std_dev=results.std_dev,
        min_score=results.min_score,
        max_score=results.max_score,
        score_distribution=results.score_distribution,
        total_cost=results.total_cost,
        total_tokens=results.total_tokens,
        execution_time_seconds=execution_time,
        results=result_items,
        quick_insight=quick_insight,  # NEW
    )
```

**Step 4: 서버 실행 테스트**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project/backend && python -c "from app.services.survey import SurveyService; print('SurveyService OK')"`

Expected: `SurveyService OK`

**Step 5: Commit**

```bash
git add backend/app/services/survey.py
git commit -m "feat(survey): integrate QuickAnalyzer into survey execution"
```

---

## Task 5: Frontend 타입 추가

**Files:**
- Modify: `frontend/src/lib/types.ts:1-440`

**Step 1: QuickInsight 타입 추가**

파일에 새 인터페이스 추가 (SurveyResponse 정의 전):

```typescript
// Quick Insight types for free tier
export interface PainPointPreview {
  rank: number;
  title: string;
  category: string;
  is_unlocked: boolean;
  description?: string;
  affected_percentage?: number;
}

export interface QuickInsight {
  one_liner: string;
  pain_points: PainPointPreview[];
  generated_at: string;
}
```

**Step 2: SurveyResponse에 quick_insight 필드 추가**

```typescript
export interface SurveyResponse {
  survey_id: string;
  product_description: string;
  sample_size: number;
  mean_score: number;
  median_score: number;
  std_dev: number;
  min_score: number;
  max_score: number;
  score_distribution: Record<string, number>;
  total_cost: number;
  total_tokens: number;
  execution_time_seconds: number;
  results: SurveyResultItem[];
  quick_insight?: QuickInsight;  // NEW
  created_at: string;
}
```

**Step 3: TypeScript 컴파일 확인**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project/frontend && npx tsc --noEmit 2>&1 | head -20`

Expected: No errors related to types.ts

**Step 4: Commit**

```bash
git add frontend/src/lib/types.ts
git commit -m "feat(types): add QuickInsight and PainPointPreview types"
```

---

## Task 6: QuickInsightCard 컴포넌트 생성

**Files:**
- Create: `frontend/src/components/survey/QuickInsightCard.tsx`

**Step 1: 컴포넌트 작성**

```tsx
"use client";

import { AlertTriangle, Lock, Sparkles, Zap } from "lucide-react";
import type { QuickInsight } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface QuickInsightCardProps {
  insight: QuickInsight;
  onUpgradeClick?: () => void;
}

const categoryColors: Record<string, string> = {
  Price: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  UX: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  Trust: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  Feature: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  Convenience: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  Other: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

const categoryLabels: Record<string, string> = {
  Price: "가격",
  UX: "사용성",
  Trust: "신뢰도",
  Feature: "기능",
  Convenience: "편의성",
  Other: "기타",
};

export function QuickInsightCard({ insight, onUpgradeClick }: QuickInsightCardProps) {
  return (
    <Card className="border-2 border-dashed border-primary/30 bg-gradient-to-br from-primary/5 to-transparent">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Sparkles className="h-5 w-5 text-primary" />
          AI 인사이트 미리보기
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* One-liner insight */}
        <div className="rounded-lg bg-primary/10 p-4">
          <div className="flex items-start gap-2">
            <Zap className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
            <p className="text-sm font-medium leading-relaxed">
              {insight.one_liner}
            </p>
          </div>
        </div>

        {/* Pain Points */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            발견된 주요 문제점 ({insight.pain_points.length}개)
          </h4>

          <div className="space-y-2">
            {insight.pain_points.map((point) => (
              <div
                key={point.rank}
                className={cn(
                  "rounded-lg border p-3 transition-all",
                  point.is_unlocked
                    ? "bg-card"
                    : "bg-muted/50 opacity-75"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {point.rank}
                    </span>
                    <span className="font-medium">{point.title}</span>
                    <Badge
                      variant="secondary"
                      className={cn("text-xs", categoryColors[point.category])}
                    >
                      {categoryLabels[point.category] || point.category}
                    </Badge>
                  </div>
                  {!point.is_unlocked && (
                    <Lock className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>

                {point.is_unlocked && point.description ? (
                  <div className="mt-2 pl-8">
                    <p className="text-sm text-muted-foreground">
                      {point.description}
                    </p>
                    {point.affected_percentage !== undefined && (
                      <p className="mt-1 text-xs text-primary font-medium">
                        응답자의 {point.affected_percentage.toFixed(1)}%가 언급
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 pl-8">
                    <p className="text-sm text-muted-foreground italic">
                      AI 심층 분석에서 확인하세요
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <Button
          onClick={onUpgradeClick}
          className="w-full"
          size="lg"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          AI 심층 분석으로 해결책 확인하기
        </Button>
      </CardContent>
    </Card>
  );
}
```

**Step 2: 컴포넌트 export 확인**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project/frontend && npx tsc --noEmit 2>&1 | grep -i "QuickInsight" || echo "No QuickInsight errors"`

Expected: `No QuickInsight errors`

**Step 3: Commit**

```bash
git add frontend/src/components/survey/QuickInsightCard.tsx
git commit -m "feat(ui): add QuickInsightCard component for free tier insights"
```

---

## Task 7: ResultsDashboard에 QuickInsightCard 통합

**Files:**
- Modify: `frontend/src/components/survey/ResultsDashboard.tsx:1-97`

**Step 1: import 추가**

```tsx
import { QuickInsightCard } from "./QuickInsightCard";
import { useRouter } from "next/navigation";
```

**Step 2: router hook 추가**

컴포넌트 내부 상단에:

```tsx
export function ResultsDashboard({ results, onReset }: ResultsDashboardProps) {
  const router = useRouter();

  // ... existing code ...
}
```

**Step 3: QuickInsightCard 렌더링 추가**

`<ScoreDistribution />` 다음, `<ResponseTable />` 전에 추가:

```tsx
      <ScoreDistribution distribution={results.score_distribution} />

      {/* Quick Insight Card */}
      {results.quick_insight && (
        <QuickInsightCard
          insight={results.quick_insight}
          onUpgradeClick={() => router.push("/qie")}
        />
      )}

      <ResponseTable results={results.results} />
```

**Step 4: TypeScript 컴파일 확인**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project/frontend && npx tsc --noEmit 2>&1 | head -20`

Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/survey/ResultsDashboard.tsx
git commit -m "feat(dashboard): integrate QuickInsightCard into survey results"
```

---

## Task 8: 통합 테스트

**Files:**
- None (manual testing)

**Step 1: Backend 서버 실행**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project/backend && uvicorn app.main:app --reload --port 8000 &`

Expected: Server starts on port 8000

**Step 2: Frontend 서버 실행**

Run: `cd /Users/smartnewbie/Desktop/SSR_Research/my-project/frontend && npm run dev &`

Expected: Server starts on port 3000

**Step 3: API 직접 테스트**

Run:
```bash
curl -X POST http://localhost:8000/api/surveys \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Test product for insight generation",
    "sample_size": 20,
    "use_mock": true,
    "model": "gpt-5-nano"
  }' | jq '.quick_insight'
```

Expected: JSON with `one_liner` and `pain_points` array (or null for mock)

**Step 4: UI 테스트**

1. 브라우저에서 http://localhost:3000 접속
2. 설문 실행 (sample_size >= 10, use_mock=false)
3. 결과 화면에서 "AI 인사이트 미리보기" 카드 확인
4. Pain Points 1개만 상세 표시, 나머지 2개는 잠김 확인
5. "AI 심층 분석으로 해결책 확인하기" 버튼 클릭 시 /qie 이동 확인

**Step 5: Final Commit**

```bash
git add -A
git commit -m "feat: complete QuickInsight integration for free tier survey results

- Add QuickInsight and PainPointPreview models
- Extract Tier1Tagger as reusable module
- Implement QuickAnalyzer for lightweight insight generation
- Integrate into SurveyService pipeline
- Add frontend QuickInsightCard component
- Show 1 unlocked + 2 locked pain points to drive upgrade"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Backend 데이터 모델 | `backend/app/models/response.py` |
| 2 | Tier1 태깅 분리 | `src/insights/tier1_tagger.py` |
| 3 | QuickAnalyzer 구현 | `src/insights/quick_analyzer.py` |
| 4 | SurveyService 통합 | `backend/app/services/survey.py` |
| 5 | Frontend 타입 | `frontend/src/lib/types.ts` |
| 6 | QuickInsightCard | `frontend/src/components/survey/QuickInsightCard.tsx` |
| 7 | Dashboard 통합 | `frontend/src/components/survey/ResultsDashboard.tsx` |
| 8 | 통합 테스트 | Manual testing |

**예상 비용:** 설문당 추가 ~$0.01-0.02 (gpt-5-mini Tier1 + 요약)
**예상 시간 증가:** +10-20초 (응답 수에 따라)
