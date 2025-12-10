"""
Base interfaces for AI chat clients.

Provides a lightweight protocol for sending chat-style messages to an AI
provider while keeping a consistent response shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Role = Literal["system", "user", "assistant"]


@dataclass(slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(slots=True)
class AIResponse:
    message: ChatMessage
    raw: Any | None = None
    usage: dict[str, Any] | None = None
    model: str | None = None


class BaseAIClient:
    """Minimal async interface for chat-based AI providers."""

    async def __aenter__(self) -> "BaseAIClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:  # pragma: no cover - noop hook
        return None

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIResponse:
        raise NotImplementedError

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """Stream the chat response token by token."""
        raise NotImplementedError

    async def embed(self, text: str, *, model: str | None = None) -> list[float]:
        """Return a single embedding for the given text."""
        raise NotImplementedError

    async def embed_batch(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        """Return embeddings for a batch of texts."""
        raise NotImplementedError
