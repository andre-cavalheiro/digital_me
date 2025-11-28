from __future__ import annotations

from typing import Any, Sequence

from fury_api.domain.content.models import Content
from fury_api.domain.conversations.models import ContextSelection, Message
from fury_api.domain.documents.models import DocumentContent
from fury_api.lib.integrations.base_ai import ChatMessage


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def build_system_prompt(
    base_prompt: str,
    *,
    sections: Sequence[DocumentContent],
    contents: Sequence[Content],
    selection: ContextSelection | None,
    max_section_chars: int,
    max_content_chars: int,
) -> tuple[str, dict[str, Any]]:
    metadata: dict[str, Any] = {
        "sections": [],
        "contents": [],
        "selection": selection.model_dump() if selection else None,
    }

    context_lines: list[str] = []

    if selection and selection.text:
        context_lines.append("User selection:")
        context_lines.append(_truncate(selection.text.strip(), max_section_chars))

    if sections:
        context_lines.append("Document sections:")
        for section in sections:
            title = section.title or f"Section {section.order_index}"
            context_lines.append(f"- {title}: {_truncate(section.content, max_section_chars)}")
            metadata["sections"].append(
                {
                    "id": section.id,
                    "order_index": section.order_index,
                    "title": section.title,
                    "word_count": section.word_count,
                }
            )

    if contents:
        context_lines.append("Related sources:")
        for item in contents:
            title = item.title or item.external_url or f"Content {item.id}"
            body = item.excerpt or item.body
            context_lines.append(f"- {title}: {_truncate(body, max_content_chars)}")
            metadata["contents"].append(
                {
                    "id": item.id,
                    "title": item.title,
                    "external_url": item.external_url,
                }
            )

    system_prompt = base_prompt.strip()
    if context_lines:
        system_prompt = f"{system_prompt}\n\nContext:\n" + "\n".join(context_lines)

    return system_prompt, metadata


def build_chat_messages(
    *,
    base_prompt: str,
    history: Sequence[Message],
    user_message: Message,
    sections: Sequence[DocumentContent],
    contents: Sequence[Content],
    selection: ContextSelection | None,
    max_section_chars: int,
    max_content_chars: int,
) -> tuple[list[ChatMessage], dict[str, Any]]:
    system_prompt, metadata = build_system_prompt(
        base_prompt,
        sections=sections,
        contents=contents,
        selection=selection,
        max_section_chars=max_section_chars,
        max_content_chars=max_content_chars,
    )

    chat_messages = [ChatMessage(role="system", content=system_prompt)]
    for message in sorted(history, key=lambda m: (m.created_at, m.id or 0)):
        chat_messages.append(ChatMessage(role=message.role, content=message.content))
    chat_messages.append(ChatMessage(role="user", content=user_message.content))

    return chat_messages, metadata
