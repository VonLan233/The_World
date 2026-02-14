"""AI subsystem — three-tier dialogue generation."""

from the_world.ai.integration import AIIntegration
from the_world.ai.router import generate_response
from the_world.ai.types import AIContext, AIResponse, AITier, InteractionType

__all__ = [
    "AIContext",
    "AIIntegration",
    "AIResponse",
    "AITier",
    "InteractionType",
    "generate_response",
]
