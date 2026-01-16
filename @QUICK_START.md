# 🚀 SSR Market Research Platform - Quick Start Guide

## ✅ 서비스 실행 중

### Backend (FastAPI)
- URL: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 상태: ✅ Running

### Frontend (Next.js)
- URL: http://localhost:3000
- 상태: ✅ Running

## 📝 사용 방법

### 1. 워크플로우 시작

브라우저에서 다음 URL 접속:
```
http://localhost:3000
```

"Run Survey" 버튼 클릭

### 2. 7단계 워크플로우

#### Step 1: Product Description
- 제품명, 카테고리, 설명 입력
- "Get AI Help" 버튼 클릭하면 GPT가 자동 완성
- "Continue to Persona Building" 클릭

#### Step 2: Core Persona Builder (7 Fields)
필수 입력 항목:
1. **Age Range**: 예) 25 ~ 45
2. **Gender Distribution**: 예) Female 55%, Male 45%
3. **Income Brackets**: 예) Low 20%, Mid 60%, High 20%
4. **Location**: Urban / Suburban / Rural
5. **Category Usage**: High / Medium / Low
6. **Shopping Behavior**: Smart Shopper / Quality Focused / Budget / Impulsive
7. **Pain Points**: 최소 1개 (예: "Time management challenges")
8. **Decision Drivers**: 최소 1개 (예: "Efficiency")

**Optional - Gemini Research**:
- "Generate Gemini Research Prompt" 클릭
- 프롬프트 복사 → Gemini Deep Research 실행
- 결과를 "Paste Report" 탭에 붙여넣기
- "Parse Report & Update Persona" 클릭
- AI가 자동으로 페르소나 개선

#### Step 3: Confirm Persona
- 입력한 페르소나 확인
- "Confirm & Continue" 클릭

#### Step 4: Sample Size Selection
다음 중 선택:
- 100 personas ($0.50, ~1 min)
- 500 personas ($2.50, ~4 min)
- 1,000 personas ($5.00, ~8 min)
- 5,000 personas ($25.00, ~40 min)
- 10,000 personas ($50.00, ~80 min)

**권장**: 처음에는 100으로 시작

#### Step 5: Generating Personas
- 자동으로 페르소나 variations 생성
- 실시간 진행률 표시
- 완료되면 자동으로 다음 단계

#### Step 6: Executing Survey
- 각 페르소나가 제품 리뷰
- SSR (Semantic Similarity Rating) 점수 계산
- 실시간 진행률 표시
- 완료되면 자동으로 결과 페이지

#### Step 7: Results Dashboard
확인 가능한 정보:
- **Mean SSR Score**: 평균 구매 의향
- **Median Score**: 중앙값
- **Std Deviation**: 표준편차
- **Score Distribution**: 점수 분포 차트
- **Sample Responses**: 개별 응답 (인구통계 + 텍스트 + 점수)

## 🧪 테스트용 예제 데이터

### Product Description
```
Name: TaskMaster Pro
Category: Productivity Software
Description: A powerful task management tool designed for busy professionals who need to stay organized and efficient
Features:
  - Real-time collaboration
  - AI-powered task prioritization
  - Cross-platform sync
  - Advanced analytics
Price: $19.99/month
Target Market: Professionals aged 25-45 who value productivity
```

### Core Persona
```
Age Range: 25 - 45
Gender: Female 55%, Male 45%
Income: Low 20%, Mid 60%, High 20%
Location: Urban
Category Usage: High (Daily)
Shopping Behavior: Smart Shopper
Pain Points:
  - Time management challenges
  - Information overload
  - Difficulty prioritizing tasks
Decision Drivers:
  - Efficiency and time savings
  - Value for money
  - User-friendly interface
```

## 🔍 API 직접 테스트

### 워크플로우 생성
```bash
curl -X POST http://localhost:8000/api/workflows
```

### Product Description AI 도움
```bash
curl -X POST "http://localhost:8000/api/workflows/products/assist?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "TaskMaster Pro",
    "brief_description": "A productivity tool",
    "target_audience": "professionals"
  }'
```

### Gemini Research Prompt 생성
```bash
curl -X POST "http://localhost:8000/api/research/generate-prompt?use_mock=true" \
  -H "Content-Type: application/json" \
  -d '{
    "product_category": "Productivity Software",
    "product_description": "Task management tool",
    "initial_persona_draft": {
      "age_range": [25, 45],
      "gender_distribution": {"female": 55, "male": 45},
      "income_brackets": {"low": 20, "mid": 60, "high": 20},
      "location": "urban",
      "category_usage": "high",
      "shopping_behavior": "smart_shopper",
      "key_pain_points": ["Time management"],
      "decision_drivers": ["Efficiency"]
    }
  }'
```

## 📊 결과 해석

### SSR Score 범위
- **0.0 - 0.3**: Very Unlikely (구매 의향 매우 낮음)
- **0.3 - 0.5**: Unlikely (구매 의향 낮음)
- **0.5 - 0.7**: Neutral (중립)
- **0.7 - 0.9**: Likely (구매 의향 높음)
- **0.9 - 1.0**: Very Likely (구매 의향 매우 높음)

### 권장 기준
- **Mean > 0.7**: 제품 출시 긍정적
- **Mean 0.5-0.7**: 개선 필요
- **Mean < 0.5**: 제품 컨셉 재검토 필요

## 🛠️ 서버 재시작

### Backend
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

## 📁 주요 파일

- **설계 문서**: `@redesign_plan.md`
- **구현 요약**: `@implementation_summary.md`
- **이 가이드**: `@QUICK_START.md`

## 🎯 다음 단계

1. ✅ 기본 워크플로우 테스트 완료
2. ⏳ Gemini Research 통합 테스트 (optional)
3. ⏳ 대규모 샘플 테스트 (1,000+ personas)
4. ⏳ 실제 OpenAI API 키 설정 (현재는 mock mode)

---

**문제 발생 시**: http://localhost:8000/docs 에서 API 상태 확인
