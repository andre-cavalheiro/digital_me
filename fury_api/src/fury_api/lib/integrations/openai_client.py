from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from fury_api.lib.integrations.base_ai import AIResponse, BaseAIClient, ChatMessage


class OpenAIClient(BaseAIClient):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None = None,
        default_model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        timeout: float = 30.0,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._default_model = default_model
        self._embedding_model = embedding_model
        self._client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIResponse:
        payload_messages: list[dict[str, Any]] = [{"role": m.role, "content": m.content} for m in messages]
        response = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=payload_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0].message
        return AIResponse(
            message=ChatMessage(role=choice.role, content=choice.content or ""),
            raw=response.model_dump(),
            usage=response.usage.model_dump() if response.usage else None,
            model=response.model,
        )

    async def embed(self, text: str, *, model: str | None = None) -> list[float]:
        embeddings = await self.embed_batch([text], model=model)
        return embeddings[0]

    async def embed_batch(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=model or self._embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
