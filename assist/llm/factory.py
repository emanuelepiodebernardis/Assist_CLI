from assist.core.config import ConfigLoader
from assist.llm.anthropic_client import AnthropicClient
from assist.llm.base import LLMClient
from assist.llm.mock_client import MockLLMClient


class LLMFactory:
    @staticmethod
    def create(
        provider: str = "anthropic",
    ) -> LLMClient:

        if provider == "mock":
            return MockLLMClient(
                fixture="Mock review result"
            )

        if provider == "anthropic":
            settings = ConfigLoader().load()

            return AnthropicClient(
                model=settings.model,
                temperature=settings.temperature,
            )

        raise ValueError(
            f"Unknown provider: {provider}"
        )