"""Enhanced persona generation service with distribution-aware sampling.

Multi-Archetype Stratified Sampling Pipeline (v2.0):
- Step 1: Segmentation - See research.py
- Step 2: Distribution - distribute_samples_by_archetype() (Pure Python/NumPy)
- Step 3: Enrichment - generate_enriched_personas_from_archetypes() (GPT-5-mini, verbosity: high)
"""

import os
import numpy as np
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def _get_persona_model() -> str:
    """Get persona enrichment model from environment or fallback."""
    return os.getenv("PERSONA_MODEL", os.getenv("LLM_MODEL", "gpt-5-nano"))


def _get_enrichment_model() -> str:
    """Get enrichment model for Step 3 (cost-optimized with verbosity)."""
    return os.getenv("ENRICHMENT_MODEL", "gpt-5-mini")


def _get_enrichment_verbosity() -> str:
    """Get enrichment verbosity setting (default: high for rich narratives)."""
    return os.getenv("ENRICHMENT_VERBOSITY", "high")


def generate_synthetic_sample(
    core_persona: dict,
    sample_size: int,
    random_seed: Optional[int] = None
) -> list[dict]:
    """
    Generate N personas following distributions from core persona.
    
    Key principle: Maintain statistical realism while introducing variation.
    Based on arXiv:2510.08338 methodology.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    personas = []

    age_range = core_persona.get("age_range", [25, 45])
    age_mean = (age_range[0] + age_range[1]) / 2
    age_std = (age_range[1] - age_range[0]) / 6
    ages = np.random.normal(age_mean, age_std, sample_size)
    ages = np.clip(ages, age_range[0], age_range[1]).astype(int)

    gender_dist = core_persona.get("gender_distribution", {"female": 0.5, "male": 0.5})
    gender_choices = list(gender_dist.keys())
    gender_probs = np.array(list(gender_dist.values()), dtype=np.float64)
    gender_probs = np.maximum(gender_probs, 0)
    gender_sum = gender_probs.sum()
    if gender_sum > 0:
        gender_probs = gender_probs / gender_sum
    else:
        gender_probs = np.ones(len(gender_choices)) / len(gender_choices)
    genders = np.random.choice(gender_choices, sample_size, p=gender_probs)

    income_dist = core_persona.get("income_brackets", {"none": 0.1, "low": 0.25, "mid": 0.45, "high": 0.2})
    income_choices = list(income_dist.keys())
    income_probs = np.array(list(income_dist.values()), dtype=np.float64)
    income_probs = np.maximum(income_probs, 0)
    income_sum = income_probs.sum()
    if income_sum > 0:
        income_probs = income_probs / income_sum
    else:
        income_probs = np.ones(len(income_choices)) / len(income_choices)
    income_brackets = np.random.choice(income_choices, sample_size, p=income_probs)

    # 통화별 소득 범위 설정 (일반 소비자 기준 월 가처분 소득)
    currency = core_persona.get("currency", "KRW")

    if currency == "KRW":
        # 한국 월 가처분 소득 범위 (KRW)
        # none: 무소득/학생 (0~50만원)
        # low: 저소득 (50~150만원)
        # mid: 중소득 (150~300만원)
        # high: 고소득 (300만원 이상)
        income_ranges = {
            "none": (0, 500000),
            "low": (500000, 1500000),
            "mid": (1500000, 3000000),
            "high": (3000000, 5000000)
        }
    else:  # USD
        # US monthly disposable income ranges (USD)
        # none: minimal/student ($0-$500)
        # low: low income ($500-$2,000)
        # mid: middle income ($2,000-$5,000)
        # high: high income ($5,000+)
        income_ranges = {
            "none": (0, 500),
            "low": (500, 2000),
            "mid": (2000, 5000),
            "high": (5000, 10000)
        }

    incomes = [
        np.random.randint(*income_ranges.get(bracket, income_ranges["mid"]))
        for bracket in income_brackets
    ]

    location = core_persona.get("location", "urban")
    base_category_usage = core_persona.get("category_usage", "medium")
    base_shopping_behavior = core_persona.get("shopping_behavior", "smart_shopper")
    pain_points = core_persona.get("key_pain_points", ["general concern"])
    decision_drivers = core_persona.get("decision_drivers", ["quality", "price"])

    # Generate varied category_usage distribution based on base value
    # SSR 논문: 다양한 사용자 유형이 필요 (Heavy users, Light users, Non-users)
    category_usage_dist = _get_category_usage_distribution(base_category_usage)
    category_usages = np.random.choice(
        list(category_usage_dist.keys()),
        sample_size,
        p=list(category_usage_dist.values())
    )

    # Generate varied shopping behaviors
    shopping_behavior_dist = _get_shopping_behavior_distribution(base_shopping_behavior)
    shopping_behaviors = np.random.choice(
        list(shopping_behavior_dist.keys()),
        sample_size,
        p=list(shopping_behavior_dist.values())
    )

    for i in range(sample_size):
        persona = {
            "id": f"PERSONA_{i+1:05d}",
            "age": int(ages[i]),
            "gender": genders[i],
            "income_bracket": income_brackets[i],
            "income_value": incomes[i],
            "currency": currency,
            "location": location,
            "category_usage": category_usages[i],
            "shopping_behavior": shopping_behaviors[i],
            "pain_points": _vary_pain_points(pain_points, i),
            "decision_drivers": _vary_decision_drivers(decision_drivers, i)
        }
        personas.append(persona)

    return personas


def _get_category_usage_distribution(base_usage: str) -> dict[str, float]:
    """
    Generate category usage distribution based on base value.
    SSR 논문: 다양한 사용자 유형 필요 - heavy, medium, light users
    """
    distributions = {
        "high": {"high": 0.4, "medium": 0.35, "low": 0.25},
        "medium": {"high": 0.25, "medium": 0.5, "low": 0.25},
        "low": {"high": 0.15, "medium": 0.35, "low": 0.5},
    }
    return distributions.get(base_usage, distributions["medium"])


def _get_shopping_behavior_distribution(base_behavior: str) -> dict[str, float]:
    """
    Generate shopping behavior distribution with variety.
    """
    all_behaviors = ["smart_shopper", "impulsive", "budget", "quality", "price_sensitive"]

    # Base behavior gets 40%, rest distributed among others
    dist = {}
    remaining_behaviors = [b for b in all_behaviors if b != base_behavior and b not in base_behavior]

    dist[base_behavior] = 0.4
    remaining_prob = 0.6 / len(remaining_behaviors) if remaining_behaviors else 0
    for b in remaining_behaviors:
        dist[b] = remaining_prob

    return dist


def _vary_pain_points(core_points: list[str], seed: int) -> list[str]:
    """
    Introduce realistic variation: some personas have subset of pain points.
    60% have all pain points, 40% have random subset (more variety).
    """
    rng = np.random.default_rng(seed)
    if len(core_points) <= 1 or rng.random() < 0.6:
        return core_points
    else:
        k = rng.integers(1, len(core_points) + 1)
        return list(rng.choice(core_points, k, replace=False))


def _vary_decision_drivers(core_drivers: list[str], seed: int) -> list[str]:
    """
    Introduce variation in decision drivers.
    70% have all drivers, 30% have random subset.
    """
    rng = np.random.default_rng(seed + 1000)
    if len(core_drivers) <= 1 or rng.random() < 0.7:
        return core_drivers
    else:
        k = rng.integers(1, len(core_drivers) + 1)
        return list(rng.choice(core_drivers, k, replace=False))


def enrich_persona_with_llm(
    persona: dict,
    product_context: Optional[str] = None,
    model: Optional[str] = None,
    client: Optional["openai.OpenAI"] = None,
    temperature: float = 0.8,
) -> dict:
    """
    Enrich persona with LLM-generated bio and personalized pain points.

    Hybrid approach: Python generates statistical skeleton,
    LLM adds realistic narrative details.

    Per GPT-5.2 guidelines: Uses reasoning_effort="none" to enable temperature
    for creative variation in persona generation.

    Args:
        persona: Base persona dict from generate_synthetic_sample()
        product_context: Optional product/service category for context
        model: LLM model to use (default from env or gpt-5-nano for cost efficiency)
        client: Optional OpenAI client
        temperature: Sampling temperature for diversity (default: 0.8)

    Returns:
        Enriched persona dict with 'bio' and 'personalized_concerns' fields
    """
    import openai

    if client is None:
        client = openai.OpenAI()

    model = model or _get_persona_model()
    currency = persona.get("currency", "KRW")

    if currency == "KRW":
        prompt = _create_korean_enrichment_prompt(persona, product_context)
    else:
        prompt = _create_english_enrichment_prompt(persona, product_context)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        reasoning_effort="none",
        temperature=temperature,
    )

    bio_text = response.choices[0].message.content.strip()

    enriched = persona.copy()
    enriched["bio"] = bio_text
    enriched["enriched"] = True

    return enriched


def _create_korean_enrichment_prompt(persona: dict, product_context: Optional[str]) -> str:
    """한국어 enrichment 프롬프트 생성."""
    gender_text = {"female": "여성", "male": "남성"}
    income_formatted = f"{persona['income_value']:,}원"

    context_line = ""
    if product_context:
        context_line = f"\n관련 서비스/제품: {product_context}"

    return f"""다음 프로필의 대학생이 가질 법한 '구체적인 고민'과 '현재 상황'을 1인칭 시점의 자연스러운 한국어로 2~3문장 작성해주세요.

[프로필]
- 나이: {persona['age']}세
- 성별: {gender_text.get(persona['gender'], persona['gender'])}
- 월 가처분 소득: 약 {income_formatted}
- 소비 성향: {persona['shopping_behavior']}
- 기존 고민: {', '.join(persona['pain_points'])}{context_line}

[규칙]
- 숫자(나이, 소득)를 직접 언급하지 마세요
- 자연스러운 구어체로 작성하세요
- 해당 인물의 경제적 상황과 라이프스타일을 반영하세요"""


def _create_english_enrichment_prompt(persona: dict, product_context: Optional[str]) -> str:
    """영어 enrichment 프롬프트 생성."""
    income_formatted = f"${persona['income_value']:,}"

    context_line = ""
    if product_context:
        context_line = f"\nRelevant product/service: {product_context}"

    return f"""Write 2-3 sentences describing the specific concerns and current situation of a person with this profile, in first-person perspective.

[Profile]
- Age: {persona['age']}
- Gender: {persona['gender']}
- Monthly disposable income: approximately {income_formatted}
- Shopping behavior: {persona['shopping_behavior']}
- Core concerns: {', '.join(persona['pain_points'])}{context_line}

[Rules]
- Do not explicitly mention numbers (age, income)
- Write in natural conversational language
- Reflect this person's financial situation and lifestyle"""


def enrich_personas_batch(
    personas: list[dict],
    product_context: Optional[str] = None,
    model: Optional[str] = None,
    max_workers: int = 5,
    temperature: float = 0.8,
) -> list[dict]:
    """
    Batch enrich multiple personas with LLM-generated content.

    Uses parallel execution for efficiency.

    Args:
        personas: List of base persona dicts
        product_context: Optional product/service category
        model: LLM model to use (default from env or gpt-5-nano)
        max_workers: Max parallel API calls
        temperature: Sampling temperature for diversity (default: 0.8)

    Returns:
        List of enriched personas
    """
    import openai

    model = model or _get_persona_model()
    client = openai.OpenAI()
    enriched_personas = [None] * len(personas)

    def enrich_single(idx: int, persona: dict) -> tuple[int, dict]:
        enriched = enrich_persona_with_llm(
            persona, product_context, model, client, temperature
        )
        return idx, enriched

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(enrich_single, i, p): i
            for i, p in enumerate(personas)
        }

        for future in as_completed(futures):
            idx, enriched = future.result()
            enriched_personas[idx] = enriched

    return enriched_personas


def persona_to_system_prompt(persona: dict) -> str:
    """
    Convert persona dict to LLM system prompt (SSR 논문 방식).
    통화에 따라 한국어/영어 프롬프트 생성.
    """
    currency = persona.get("currency", "KRW")

    if currency == "KRW":
        return _generate_korean_prompt(persona)
    else:
        return _generate_english_prompt(persona)


def _generate_korean_prompt(persona: dict) -> str:
    """한국어 시스템 프롬프트 생성."""
    usage_text = {
        "high": "자주 사용하며 익숙함",
        "medium": "가끔 사용해본 경험 있음",
        "low": "거의 사용해본 적 없음"
    }

    behavior_text = {
        "impulsive": "마음에 들면 즉흥적으로 결제하기도 함",
        "budget": "한정된 예산 안에서만 소비함",
        "quality": "가격보다 품질과 신뢰도를 중요하게 생각함",
        "smart_shopper": "여러 서비스를 꼼꼼히 비교 분석한 뒤 결정함",
        "price_sensitive": "가격에 매우 민감하며 가성비를 최우선으로 따짐"
    }

    gender_text = {"female": "여성", "male": "남성"}
    location_text = {"urban": "도심", "suburban": "중소도시", "rural": "지방", "mixed": "전국"}

    income_formatted = f"{persona['income_value']:,}원"

    # LLM enriched bio가 있으면 사용
    bio_section = ""
    if persona.get("bio"):
        bio_section = f"""

[나의 이야기]
{persona['bio']}"""

    return f"""[역할 정의]
당신은 대한민국 {location_text.get(persona['location'], '도심')}에 거주하는 {persona['age']}세 {gender_text.get(persona['gender'], persona['gender'])} 대학생입니다.

[경제적 상황]
- 월 가처분 소득(용돈+알바비): 약 {income_formatted}
- 소비 성향: {behavior_text.get(persona['shopping_behavior'], '합리적인 소비를 지향함')}

[카테고리 사용 경험]
- 제품/서비스 사용 경험: {usage_text.get(persona['category_usage'], '보통')}

[핵심 가치관 및 걱정]
당신이 제품/서비스를 선택할 때 중요하게 생각하거나 걱정하는 점:
{chr(10).join(f'- {p}' for p in persona['pain_points'])}

구매/가입 결정에 영향을 미치는 요소:
{chr(10).join(f'- {d}' for d in persona['decision_drivers'])}{bio_section}

[지시사항]
위 페르소나에 완전히 몰입하세요. 제시되는 제품/서비스 컨셉을 보고, 당신의 경제적 상황과 가치관에 비추어 솔직하게 답변하세요. 나이나 소득을 직접 언급하지 말고, 자연스러운 구어체로 응답하세요."""


def _generate_english_prompt(persona: dict) -> str:
    """영어 시스템 프롬프트 생성 (USD용)."""
    usage_text = {
        "high": "frequently uses and is familiar with",
        "medium": "occasionally uses",
        "low": "rarely or never uses"
    }

    behavior_text = {
        "impulsive": "tends to make impulse purchases when something catches their eye",
        "budget": "strictly stays within a limited budget",
        "quality": "prioritizes quality and reliability over price",
        "smart_shopper": "carefully compares multiple options before deciding",
        "price_sensitive": "highly price-conscious and prioritizes value for money"
    }

    gender_text = {"female": "female", "male": "male"}
    location_text = {"urban": "urban area", "suburban": "suburban area", "rural": "rural area", "mixed": "various locations"}

    income_formatted = f"${persona['income_value']:,}"

    # LLM enriched bio가 있으면 사용
    bio_section = ""
    if persona.get("bio"):
        bio_section = f"""

[My Story]
{persona['bio']}"""

    return f"""[Role Definition]
You are a {persona['age']}-year-old {gender_text.get(persona['gender'], persona['gender'])} living in a {location_text.get(persona['location'], 'urban area')}.

[Financial Situation]
- Monthly disposable income: approximately {income_formatted}
- Shopping tendency: {behavior_text.get(persona['shopping_behavior'], 'makes rational purchasing decisions')}

[Category Experience]
- Product/service usage: {usage_text.get(persona['category_usage'], 'moderate')}

[Core Values and Concerns]
What you consider important or worry about when choosing products/services:
{chr(10).join(f'- {p}' for p in persona['pain_points'])}

Factors that influence your purchase decisions:
{chr(10).join(f'- {d}' for d in persona['decision_drivers'])}{bio_section}

[Instructions]
Fully immerse yourself in this persona. When presented with a product/service concept, respond honestly based on your financial situation and values. Do not explicitly mention your age or income, and respond in natural conversational language."""


def calculate_distribution_stats(personas: list[dict]) -> dict:
    """Calculate distribution statistics for generated personas."""
    ages = [p["age"] for p in personas]
    genders = [p["gender"] for p in personas]
    incomes = [p["income_bracket"] for p in personas]

    gender_counts = {}
    for g in genders:
        gender_counts[g] = gender_counts.get(g, 0) + 1

    income_counts = {}
    for i in incomes:
        income_counts[i] = income_counts.get(i, 0) + 1

    return {
        "age": {
            "mean": float(np.mean(ages)),
            "std": float(np.std(ages)),
            "min": int(np.min(ages)),
            "max": int(np.max(ages))
        },
        "gender": gender_counts,
        "income": income_counts
    }


# =============================================================================
# Multi-Archetype Stratified Sampling Pipeline (v2.0)
# =============================================================================


def distribute_samples_by_archetype(
    archetypes: list[dict],
    total_samples: int = 1000,
) -> list[dict]:
    """
    Step 2: Distribution - 수학적 비율 배분 (No LLM, Pure Python/NumPy).

    정의된 share_ratio에 따라 전체 표본(N)을 그룹별로 할당합니다.
    할루시네이션 원천 차단을 위해 LLM을 사용하지 않습니다.

    Args:
        archetypes: Step 1에서 생성된 Archetype 리스트 (share_ratio 포함)
        total_samples: 생성할 총 페르소나 수 (기본값: 1000)

    Returns:
        distribution_plan: 각 archetype별 할당 수가 포함된 리스트
    """
    distribution_plan = []
    allocated = 0

    sorted_archetypes = sorted(
        archetypes,
        key=lambda x: x.get("share_ratio", 0),
        reverse=True
    )

    for i, archetype in enumerate(sorted_archetypes):
        share_ratio = archetype.get("share_ratio", 0)

        if i == len(sorted_archetypes) - 1:
            count = total_samples - allocated
        else:
            count = int(total_samples * share_ratio)

        allocated += count

        distribution_plan.append({
            "segment_id": archetype.get("segment_id", f"SEGMENT_{i+1:02d}"),
            "segment_name": archetype.get("segment_name", f"Segment {i+1}"),
            "archetype": archetype,
            "count": count,
            "share_ratio": share_ratio,
            "actual_ratio": count / total_samples,
        })

    return distribution_plan


def generate_personas_for_archetype(
    archetype: dict,
    count: int,
    start_id: int = 0,
    currency: str = "KRW",
    random_seed: Optional[int] = None,
) -> list[dict]:
    """
    단일 Archetype에 대한 페르소나 N개 생성 (Step 3 전처리).

    Archetype의 속성(연령대, 성별 분포, 소득 수준 등)을 유지하면서
    개별 페르소나의 변이를 생성합니다.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    personas = []

    demographics = archetype.get("demographics", {})
    age_range = demographics.get("age_range", [20, 30])
    age_mean = (age_range[0] + age_range[1]) / 2
    age_std = (age_range[1] - age_range[0]) / 6
    ages = np.random.normal(age_mean, age_std, count)
    ages = np.clip(ages, age_range[0], age_range[1]).astype(int)

    gender_dist = demographics.get("gender_distribution", {"female": 50, "male": 50})
    gender_choices = list(gender_dist.keys())
    gender_probs = np.array([gender_dist.get(g, 50) for g in gender_choices], dtype=np.float64)
    gender_probs = gender_probs / gender_probs.sum()
    genders = np.random.choice(gender_choices, count, p=gender_probs)

    income_level = archetype.get("income_level", "mid")
    income_dist = _get_income_distribution_for_level(income_level)
    income_choices = list(income_dist.keys())
    income_probs = np.array(list(income_dist.values()), dtype=np.float64)
    income_brackets = np.random.choice(income_choices, count, p=income_probs)

    if currency == "KRW":
        income_ranges = {
            "none": (0, 500000),          # 0~50만원
            "low": (500000, 1500000),     # 50~150만원
            "mid": (1500000, 3000000),    # 150~300만원
            "high": (3000000, 5000000)    # 300만원+
        }
    else:
        income_ranges = {
            "none": (0, 500),             # $0~500
            "low": (500, 2000),           # $500~2000
            "mid": (2000, 5000),          # $2000~5000
            "high": (5000, 10000)         # $5000+
        }

    incomes = [
        np.random.randint(*income_ranges.get(bracket, income_ranges["mid"]))
        for bracket in income_brackets
    ]

    base_category_usage = archetype.get("category_usage", "medium")
    category_usage_dist = _get_category_usage_distribution(base_category_usage)
    category_usages = np.random.choice(
        list(category_usage_dist.keys()),
        count,
        p=list(category_usage_dist.values())
    )

    base_shopping_behavior = archetype.get("shopping_behavior", "smart_shopper")
    shopping_behavior_dist = _get_shopping_behavior_distribution(base_shopping_behavior)
    shopping_behaviors = np.random.choice(
        list(shopping_behavior_dist.keys()),
        count,
        p=list(shopping_behavior_dist.values())
    )

    location = archetype.get("location", "urban")
    core_traits = archetype.get("core_traits", [])
    pain_points = archetype.get("pain_points", ["general concern"])
    decision_drivers = archetype.get("decision_drivers", ["quality", "price"])

    for i in range(count):
        persona = {
            "id": f"PERSONA_{start_id + i + 1:05d}",
            "segment_id": archetype.get("segment_id"),
            "segment_name": archetype.get("segment_name"),
            "age": int(ages[i]),
            "gender": genders[i],
            "income_bracket": income_brackets[i],
            "income_value": incomes[i],
            "currency": currency,
            "location": location,
            "category_usage": category_usages[i],
            "shopping_behavior": shopping_behaviors[i],
            "core_traits": core_traits,
            "pain_points": _vary_pain_points(pain_points, start_id + i),
            "decision_drivers": _vary_decision_drivers(decision_drivers, start_id + i),
        }
        personas.append(persona)

    return personas


def _get_income_distribution_for_level(income_level: str) -> dict[str, float]:
    """소득 레벨에 따른 소득 분포 생성."""
    distributions = {
        "none": {"none": 0.6, "low": 0.3, "mid": 0.1, "high": 0.0},
        "low": {"none": 0.2, "low": 0.5, "mid": 0.25, "high": 0.05},
        "mid": {"none": 0.05, "low": 0.2, "mid": 0.55, "high": 0.2},
        "high": {"none": 0.0, "low": 0.1, "mid": 0.3, "high": 0.6},
    }
    return distributions.get(income_level, distributions["mid"])


def enrich_persona_with_llm_v2(
    persona: dict,
    product_context: Optional[str] = None,
    model: Optional[str] = None,
    client: Optional["openai.OpenAI"] = None,
    temperature: float = 0.8,
) -> dict:
    """
    Step 3: Enrichment - GPT-5-mini + verbosity: high로 풍부한 서사 생성.

    GPT-5.2 계열의 verbosity 파라미터를 활용하여 페르소나의 Bio와
    사연을 구체적이고 길게 서술합니다.

    Per GPT-5.2 guidelines:
    - reasoning: none (단순 창작 작업이므로 추론 대기 시간 제거)
    - verbosity: high (풍부한 데이터 생성)
    - temperature: 0.8 (다양성 확보, reasoning=none일 때만 가능)

    Args:
        persona: 기본 페르소나 dict
        product_context: 제품/서비스 카테고리 컨텍스트
        model: 사용할 모델 (기본값: gpt-5-mini)
        client: OpenAI 클라이언트
        temperature: 샘플링 온도 (기본값: 0.8)

    Returns:
        Enriched persona dict with 'bio' field
    """
    import openai

    if client is None:
        client = openai.OpenAI()

    model = model or _get_enrichment_model()
    verbosity = _get_enrichment_verbosity()
    currency = persona.get("currency", "KRW")

    if currency == "KRW":
        prompt = _create_korean_enrichment_prompt_v2(persona, product_context)
    else:
        prompt = _create_english_enrichment_prompt_v2(persona, product_context)

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=400,
        reasoning={"effort": "none"},
        text={"verbosity": verbosity},
        temperature=temperature,
    )

    bio_text = response.output_text.strip()

    enriched = persona.copy()
    enriched["bio"] = bio_text
    enriched["enriched"] = True
    enriched["enrichment_model"] = model

    return enriched


def _create_korean_enrichment_prompt_v2(persona: dict, product_context: Optional[str]) -> str:
    """Step 3용 한국어 enrichment 프롬프트 (High Verbosity 모드)."""
    gender_text = {"female": "여성", "male": "남성"}
    income_formatted = f"{persona['income_value']:,}원"

    traits_text = ""
    if persona.get("core_traits"):
        traits_text = f"\n- 핵심 특성: {', '.join(persona['core_traits'])}"

    context_line = ""
    if product_context:
        context_line = f"\n관련 서비스/제품: {product_context}"

    segment_info = ""
    if persona.get("segment_name"):
        segment_info = f"\n- 소비자 유형: {persona['segment_name']}"

    return f"""너는 창의적인 작가야. 다음 프로필의 인물이 가질 법한 '구체적인 배경 스토리'와 '현재 상황', '고민'을 1인칭 시점의 자연스러운 한국어로 아주 상세하게 기술해줘.

[프로필]
- 나이: {persona['age']}세
- 성별: {gender_text.get(persona['gender'], persona['gender'])}
- 월 가처분 소득: 약 {income_formatted}
- 소비 성향: {persona['shopping_behavior']}
- 제품/서비스 사용 경험: {persona['category_usage']}{segment_info}{traits_text}
- 기존 고민: {', '.join(persona['pain_points'])}
- 구매 결정 요인: {', '.join(persona['decision_drivers'])}{context_line}

[지시사항]
- 'High Verbosity' 모드이므로, 유저의 배경 스토리를 아주 상세하게 기술해줘
- 숫자(나이, 소득)를 직접 언급하지 마
- 자연스러운 구어체로 작성해
- 해당 인물의 경제적 상황과 라이프스타일, 가치관을 생생하게 반영해
- 이 인물만의 구체적인 사연과 말투를 창작해"""


def _create_english_enrichment_prompt_v2(persona: dict, product_context: Optional[str]) -> str:
    """Step 3용 영어 enrichment 프롬프트 (High Verbosity 모드)."""
    income_formatted = f"${persona['income_value']:,}"

    traits_text = ""
    if persona.get("core_traits"):
        traits_text = f"\n- Core traits: {', '.join(persona['core_traits'])}"

    context_line = ""
    if product_context:
        context_line = f"\nRelevant product/service: {product_context}"

    segment_info = ""
    if persona.get("segment_name"):
        segment_info = f"\n- Consumer type: {persona['segment_name']}"

    return f"""You are a creative writer. Create a detailed background story, current situation, and concerns for a person with this profile, written in first-person perspective with rich narrative detail.

[Profile]
- Age: {persona['age']}
- Gender: {persona['gender']}
- Monthly disposable income: approximately {income_formatted}
- Shopping behavior: {persona['shopping_behavior']}
- Category usage: {persona['category_usage']}{segment_info}{traits_text}
- Core concerns: {', '.join(persona['pain_points'])}
- Purchase decision factors: {', '.join(persona['decision_drivers'])}{context_line}

[Instructions]
- This is 'High Verbosity' mode, so write a very detailed background story
- Do not explicitly mention numbers (age, income)
- Write in natural conversational language
- Vividly reflect this person's financial situation, lifestyle, and values
- Create a unique personal story and speaking style for this individual"""


def enrich_personas_batch_v2(
    personas: list[dict],
    product_context: Optional[str] = None,
    model: Optional[str] = None,
    max_workers: int = 10,
    temperature: float = 0.8,
) -> list[dict]:
    """
    Step 3: Batch Enrichment - 다중 페르소나 병렬 처리.

    Args:
        personas: 기본 페르소나 리스트
        product_context: 제품/서비스 카테고리
        model: 사용할 모델 (기본값: gpt-5-mini)
        max_workers: 최대 병렬 API 호출 수
        temperature: 샘플링 온도

    Returns:
        Enriched personas 리스트
    """
    import openai

    model = model or _get_enrichment_model()
    client = openai.OpenAI()
    enriched_personas = [None] * len(personas)

    def enrich_single(idx: int, persona: dict) -> tuple[int, dict]:
        enriched = enrich_persona_with_llm_v2(
            persona, product_context, model, client, temperature
        )
        return idx, enriched

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(enrich_single, i, p): i
            for i, p in enumerate(personas)
        }

        for future in as_completed(futures):
            idx, enriched = future.result()
            enriched_personas[idx] = enriched

    return enriched_personas


def generate_enriched_personas_from_archetypes(
    archetypes: list[dict],
    total_samples: int = 1000,
    product_context: Optional[str] = None,
    currency: str = "KRW",
    enrich: bool = True,
    max_workers: int = 10,
    random_seed: Optional[int] = None,
) -> dict:
    """
    Multi-Archetype Stratified Sampling 파이프라인 전체 실행.

    Step 2 (Distribution) + Step 3 (Enrichment)를 통합 실행합니다.

    Args:
        archetypes: Step 1에서 생성된 Archetype 리스트
        total_samples: 생성할 총 페르소나 수
        product_context: 제품/서비스 카테고리
        currency: 통화 (KRW 또는 USD)
        enrich: LLM enrichment 적용 여부
        max_workers: 병렬 처리 워커 수
        random_seed: 재현성을 위한 랜덤 시드

    Returns:
        dict containing:
        - personas: 생성된 전체 페르소나 리스트
        - distribution_plan: 각 archetype별 할당 정보
        - stats: 분포 통계
    """
    distribution_plan = distribute_samples_by_archetype(archetypes, total_samples)

    all_personas = []
    current_id = 0

    for plan in distribution_plan:
        archetype = plan["archetype"]
        count = plan["count"]

        segment_seed = None
        if random_seed is not None:
            segment_seed = random_seed + current_id

        segment_personas = generate_personas_for_archetype(
            archetype=archetype,
            count=count,
            start_id=current_id,
            currency=currency,
            random_seed=segment_seed,
        )

        all_personas.extend(segment_personas)
        current_id += count

    if enrich:
        all_personas = enrich_personas_batch_v2(
            personas=all_personas,
            product_context=product_context,
            max_workers=max_workers,
        )

    stats = calculate_distribution_stats(all_personas)

    segment_stats = {}
    for persona in all_personas:
        seg_id = persona.get("segment_id", "unknown")
        if seg_id not in segment_stats:
            segment_stats[seg_id] = {"count": 0, "segment_name": persona.get("segment_name")}
        segment_stats[seg_id]["count"] += 1

    return {
        "personas": all_personas,
        "distribution_plan": distribution_plan,
        "stats": stats,
        "segment_stats": segment_stats,
        "total_count": len(all_personas),
        "enriched": enrich,
    }
