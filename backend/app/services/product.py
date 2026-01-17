"""Product description service with AI assistance."""

import os
import json
from openai import AsyncOpenAI


def _get_product_model() -> str:
    """Get product model from environment or fallback."""
    return os.getenv("PRODUCT_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))


client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


async def assist_product_description(
    product_name: str,
    brief_description: str,
    target_audience: str | None = None,
) -> dict:
    """Generate AI-assisted product description.

    Args:
        product_name: Name of the product
        brief_description: Brief description of the product
        target_audience: Optional target audience description

    Returns:
        dict with suggested fields for ProductDescription
    """
    prompt = f"""You are a product marketing expert. Help improve this product description.

Product Name: {product_name}
Brief Description: {brief_description}
{f"Target Audience: {target_audience}" if target_audience else ""}

Generate a comprehensive product description with:
1. Category (e.g., "Productivity Software", "Health & Fitness App")
2. Full description (2-3 sentences, clear value proposition)
3. Key features (4-6 bullet points)
4. Price point suggestion (e.g., "$9.99/month", "Free with premium at $29.99")
5. Target market description (who would buy this)

Return ONLY a JSON object with these exact keys:
{{
  "category": "...",
  "description": "...",
  "features": ["...", "..."],
  "price_point": "...",
  "target_market": "..."
}}"""

    try:
        response = await client.chat.completions.create(
            model=_get_product_model(),
            messages=[
                {
                    "role": "system",
                    "content": "You are a product marketing expert. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")

        import json

        result = json.loads(content)

        return {
            "category": result.get("category", ""),
            "description": result.get("description", ""),
            "features": result.get("features", []),
            "price_point": result.get("price_point", ""),
            "target_market": result.get("target_market", ""),
        }

    except Exception as e:
        raise ValueError(f"Failed to generate product description: {e}")


async def assist_product_description_mock(
    product_name: str,
    brief_description: str,
    target_audience: str | None = None,
) -> dict:
    """Mock version for testing without API key."""
    return {
        "category": "Productivity Software",
        "description": f"{product_name} is a powerful tool designed to help {target_audience or 'professionals'} achieve more. {brief_description}",
        "features": [
            "Intuitive user interface",
            "Real-time collaboration",
            "Advanced analytics dashboard",
            "Mobile and desktop apps",
            "Seamless integrations",
        ],
        "price_point": "$19.99/month or $199/year",
        "target_market": f"Busy {target_audience or 'professionals'} aged 25-45 who value efficiency and quality tools",
    }


CHAT_SYSTEM_PROMPT = """당신은 제품 설명 작성을 돕는 친절한 AI 어시스턴트입니다.
사용자와 대화를 통해 다음 정보를 수집해야 합니다:
1. 제품명 (name)
2. 카테고리 (category) - 예: "소개팅 앱", "생산성 소프트웨어"
3. 제품 설명 (description) - 2-3문장의 가치 제안
4. 주요 기능 (features) - 4-6개의 핵심 기능
5. 가격대 (price_point) - 예: "9,900원/월", "무료 (프리미엄 29,900원)"
6. 타겟 시장 (target_market) - 예: "대학생 18-27세"

대화 방식:
- 한국어로 친근하게 대화하세요
- 한 번에 1-2개의 질문만 하세요
- 사용자가 모호하게 답하면 구체적으로 물어보세요
- 충분한 정보가 모이면 정리된 내용을 보여주고 확인을 요청하세요

응답 형식 (JSON):
{
  "message": "사용자에게 보여줄 메시지",
  "extracted_data": null 또는 {
    "name": "...",
    "category": "...",
    "description": "...",
    "features": ["...", "..."],
    "price_point": "...",
    "target_market": "..."
  }
}

extracted_data는 모든 정보가 수집되고 사용자가 확인했을 때만 포함하세요.
아직 정보 수집 중이면 extracted_data는 null로 설정하세요."""


async def chat_product_description(
    messages: list[dict],
    current_data: dict | None = None,
) -> dict:
    """Chat-based product description assistance.

    Args:
        messages: Conversation history
        current_data: Current form data if any

    Returns:
        dict with message and optional extracted_data
    """
    context = ""
    if current_data:
        context = f"\n\n현재 폼에 입력된 정보:\n{json.dumps(current_data, ensure_ascii=False, indent=2)}"

    try:
        response = await client.chat.completions.create(
            model=_get_product_model(),
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT + context},
                *[
                    {"role": m["role"], "content": m["content"]}
                    for m in messages
                ],
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")

        result = json.loads(content)

        return {
            "message": result.get("message", ""),
            "extracted_data": result.get("extracted_data"),
        }

    except Exception as e:
        raise ValueError(f"Failed to process chat: {e}")
