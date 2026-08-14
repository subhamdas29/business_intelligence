from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """
    Abstract interface for LLM operations.
    Allows easy swapping between OpenAI, Anthropic, Google Gemini, and local LLMs.
    """

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a raw text completion from the LLM."""
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, response_model: Type[T], system_prompt: str | None = None) -> T:
        """Generate a structured response adhering strictly to a Pydantic schema."""
        pass

    @abstractmethod
    async def stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        """Stream response tokens back as an async generator."""
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings."""
        pass
