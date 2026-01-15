"""Prompt templates for survey execution."""

SURVEY_USER_PROMPT_TEMPLATE = """Here is a product concept:

"{product_description}"

Based on this description, explain your thoughts on whether you would purchase
this product. Focus on your reasoning and feelings about it.

IMPORTANT: Do NOT provide a numerical rating or score. Just explain your opinion
naturally, as you would to a friend."""


SURVEY_REINFORCEMENT_TEMPLATE = """Remember: Express your genuine opinion about this product
based on your lifestyle and needs. Do NOT use numbers, ratings, or scores.
Just share your thoughts naturally."""


def create_survey_prompt(product_description: str) -> str:
    """
    Create the user prompt for product evaluation.

    Args:
        product_description: Description of the product concept

    Returns:
        Formatted user prompt
    """
    return SURVEY_USER_PROMPT_TEMPLATE.format(
        product_description=product_description
    )


def create_reinforced_prompt(product_description: str) -> str:
    """
    Create reinforced prompt (for retry after numeric response).

    Args:
        product_description: Description of the product concept

    Returns:
        Formatted prompt with stronger anti-numeric instruction
    """
    base_prompt = create_survey_prompt(product_description)
    return f"{base_prompt}\n\n{SURVEY_REINFORCEMENT_TEMPLATE}"


def create_full_prompt(
    system_prompt: str,
    product_description: str,
    reinforced: bool = False,
) -> str:
    """
    Create full prompt combining system and user prompts.

    Args:
        system_prompt: Persona system prompt
        product_description: Product concept
        reinforced: Whether to use reinforced anti-numeric prompt

    Returns:
        Combined prompt
    """
    if reinforced:
        user_prompt = create_reinforced_prompt(product_description)
    else:
        user_prompt = create_survey_prompt(product_description)

    return f"{system_prompt}\n\n{user_prompt}"
