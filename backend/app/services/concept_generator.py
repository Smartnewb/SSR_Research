"""Concept Board Generator Service.

Transforms raw product specifications into persuasive Concept Board format
following standard marketing research structure (5 Parts):
1. Headline: Eye-catching one-liner
2. Consumer Insight: Pain point/need (empathy)
3. Benefits: Value propositions (list)
4. RTB: Reasons to Believe (list)
5. Image Prompt: Visual representation description
"""

import os
import json
from openai import AsyncOpenAI

from ..models.workflow import ProductDescription
from ..models.comparison import ConceptInput


def _get_concept_model() -> str:
    """Get model for concept generation from environment."""
    return os.getenv("CONCEPT_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))


client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


CONCEPT_GENERATOR_SYSTEM_PROMPT = """You are a World-Class Marketing Copywriter.
Your goal is to transform raw product specifications into a persuasive 'Concept Board' for consumer research.

You must generate a structured JSON based on the standard 5-part concept format:

1. **Headline** (headline):
   - Catchy, emotional, under 50 characters
   - Must evoke curiosity or emotion
   - Example: "단 3일, 2단계 더 밝은 미소"

2. **Consumer Insight** (consumer_insight):
   - Start with empathy about the user's pain point
   - Use phrases like "~하지 않으셨나요?", "~때문에 고민이신가요?"
   - Example: "커피로 누렇게 변한 치아 때문에 웃기가 꺼려지시나요?"

3. **Benefits** (benefits):
   - 3 bullet points focusing on VALUE, not features
   - Each benefit should answer "So what?" from user's perspective
   - Use active verbs and specific outcomes
   - Example: ["집에서 편하게 전문가급 미백 효과를", "매일 양치만으로 3일 후 달라진 미소", "민감한 치아도 부담 없는 순한 처방"]

4. **RTB (Reason to Believe)** (rtb):
   - 2-3 technical or factual proofs
   - Include certifications, data, patents, testimonials
   - Example: ["특허 받은 과산화수소 3% 포뮬러", "100시간 수분 지속 임상 완료", "10만 고객 만족 리뷰"]

5. **Image Prompt** (image_prompt):
   - Detailed prompt for DALL-E 3 to generate product image
   - Include: product appearance, setting, lighting, style, composition
   - Example: "A sleek red toothpaste tube with white cap on a marble bathroom counter. Soft morning light, minimalist style, high-end product photography, 4K quality."

CRITICAL RULES:
- Do NOT simply copy the input - DRAMATIZE and SELL the concept!
- Write in Korean unless the product name is in English
- Make every word count - this is for consumer testing
- Benefits and RTB must be compelling, not generic
- Image prompt must be detailed enough for consistent image generation

Return ONLY valid JSON with exactly these keys:
{
  "headline": "...",
  "consumer_insight": "...",
  "benefits": ["...", "...", "..."],
  "rtb": ["...", "...", "..."],
  "image_prompt": "..."
}"""


async def generate_concept_from_product(
    product: ProductDescription,
    concept_id: str = "CONCEPT_001",
) -> ConceptInput:
    """Generate a Concept Board from product description using LLM.

    Args:
        product: ProductDescription from Step 1
        concept_id: Unique identifier for the concept

    Returns:
        ConceptInput with persuasive marketing copy
    """
    user_prompt = f"""Transform this product into a compelling Concept Board:

**Product Name:** {product.name}
**Category:** {product.category}
**Description:** {product.description}
**Key Features:** {', '.join(product.features) if product.features else 'Not specified'}
**Price:** {product.price_point or 'Not specified'}
**Target Market:** {product.target_market}

Generate a persuasive Concept Board that would make the target market want to buy this product.
Remember: Transform the raw specs into emotional, compelling marketing copy!"""

    try:
        model = _get_concept_model()
        model_lower = model.lower()

        # GPT-5 모델별 temperature 지원 여부 (OpenAI 공식 문서 기준)
        # - gpt-5, gpt-5-mini, gpt-5-nano: reasoning 기본값 medium → temperature 미지원
        # - gpt-5.1, gpt-5.2: reasoning 기본값 none → temperature 지원
        # temperature는 reasoning_effort="none"일 때만 지원됨
        older_gpt5_models = ["gpt-5-nano", "gpt-5-mini"]
        is_older_gpt5 = any(m in model_lower for m in older_gpt5_models) or model_lower == "gpt-5"

        create_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": CONCEPT_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        # older GPT-5 모델(gpt-5, gpt-5-mini, gpt-5-nano)은 temperature 미지원
        # gpt-5.1, gpt-5.2는 reasoning 기본값이 none이므로 temperature 지원
        if not is_older_gpt5:
            create_params["temperature"] = 0.8

        response = await client.chat.completions.create(**create_params)

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")

        result = json.loads(content)

        # Ensure benefits and rtb are lists
        benefits = result.get("benefits", [])
        if isinstance(benefits, str):
            benefits = [benefits]

        rtb = result.get("rtb", [])
        if isinstance(rtb, str):
            rtb = [rtb]

        # Truncate price to fit ConceptInput.price max_length (100 chars)
        price_text = product.price_point or "가격 문의"
        if len(price_text) > 97:
            price_text = price_text[:97] + "..."

        return ConceptInput(
            id=concept_id,
            title=product.name,
            headline=result.get("headline", product.name),
            consumer_insight=result.get("consumer_insight", ""),
            benefits=benefits[:5],  # Max 5
            rtb=rtb[:5],  # Max 5
            image_prompt=result.get("image_prompt", f"Product photo of {product.name}"),
            price=price_text,
        )

    except Exception as e:
        raise ValueError(f"Failed to generate concept: {e}")


async def generate_concept_from_product_mock(
    product: ProductDescription,
    concept_id: str = "CONCEPT_001",
) -> ConceptInput:
    """Mock version for testing without API key."""
    # Truncate price to fit ConceptInput.price max_length (100 chars)
    price_text = product.price_point or "가격 문의"
    if len(price_text) > 97:
        price_text = price_text[:97] + "..."

    return ConceptInput(
        id=concept_id,
        title=product.name,
        headline=f"{product.name}로 시작하는 새로운 경험",
        consumer_insight=f"{product.target_market}이신가요? 기존 제품들이 만족스럽지 않으셨다면, 이제 다른 선택이 있습니다.",
        benefits=[
            f"{product.category} 카테고리 최고의 품질",
            "간편하고 직관적인 사용법",
            "합리적인 가격으로 프리미엄 경험",
        ],
        rtb=[
            "철저한 품질 검증 완료",
            "10,000+ 사용자 만족 리뷰",
            f"{product.category} 전문가 추천",
        ],
        image_prompt=f"Professional product photography of {product.name}. Clean white background, soft studio lighting, high-end commercial style, 4K quality, minimal composition.",
        price=price_text,
    )
