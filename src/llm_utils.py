from typing import Optional

GPT5_REASONING_EFFORTS = {"minimal", "low", "medium", "high"}
GPT52_REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh"}


def is_gpt5_model(model: str) -> bool:
    return model.startswith("gpt-5")


def is_gpt52_or_51(model: str) -> bool:
    return model.startswith("gpt-5.2") or model.startswith("gpt-5.1")


def normalize_reasoning_effort(model: str, effort: Optional[str]) -> Optional[str]:
    if not model:
        return effort
    if not is_gpt5_model(model):
        return None
    if is_gpt52_or_51(model):
        return effort if effort in GPT52_REASONING_EFFORTS else "none"
    return effort if effort in GPT5_REASONING_EFFORTS else "minimal"


def can_use_temperature(model: str, reasoning_effort: Optional[str]) -> bool:
    if not is_gpt5_model(model):
        return True
    if is_gpt52_or_51(model):
        return reasoning_effort == "none"
    return False


def get_max_tokens_param(model: str, value: int) -> dict:
    if is_gpt5_model(model):
        return {"max_completion_tokens": value}
    return {"max_tokens": value}
