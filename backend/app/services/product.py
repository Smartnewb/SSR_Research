"""Product description service with AI assistance."""

import os
from openai import AsyncOpenAI


def _get_product_model() -> str:
    """Get product model from environment or fallback."""
    return os.getenv("PRODUCT_MODEL", os.getenv("LLM_MODEL", "gpt-5-nano"))


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
