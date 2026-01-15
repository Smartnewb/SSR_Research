"""Persona generation module for synthetic respondents."""

from .generator import (
    Persona,
    generate_persona_template,
    generate_persona_hybrid,
    generate_personas_stratified,
    generate_personas_targeted,
    persona_to_system_prompt,
)
from .templates import TEMPLATES
from .validator import validate_persona, validate_personas_batch

__all__ = [
    "Persona",
    "generate_persona_template",
    "generate_persona_hybrid",
    "generate_personas_stratified",
    "generate_personas_targeted",
    "persona_to_system_prompt",
    "TEMPLATES",
    "validate_persona",
    "validate_personas_batch",
]
