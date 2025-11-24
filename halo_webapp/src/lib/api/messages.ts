import { env } from "@/app/env"
import { api } from "./client"
import { withMock, mockMessages } from "./mocks"
import { messageSchema } from "./schemas/message"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { Message, MessageContext, MessageRole } from "./types"

export async function fetchMessages(conversationId: number): Promise<Message[]> {
  return withMock(
    mockMessages.filter((m) => m.conversation_id === conversationId),
    async () => {
      const response = await api.get(`/conversations/${conversationId}/messages`)
      const paginatedSchema = paginatedResponseSchema(messageSchema)
      const parsed = paginatedSchema.parse(response.data)
      return parsed.items
    },
  )
}

export async function sendMessage(
  conversationId: number,
  payload: { content: string; role?: MessageRole; context_sources?: MessageContext }
): Promise<Message> {
  return withMock(
    (() => {
      const nextId = Math.max(...mockMessages.map((m) => m.id)) + 1
      const created: Message = {
        id: nextId,
        conversation_id: conversationId,
        role: payload.role ?? "user",
        content: payload.content,
        created_at: new Date().toISOString(),
        status: "completed",
        metadata: { mock: true },
      }
      mockMessages.push(created)
      return created
    })(),
    async () => {
      const response = await api.post<Message>(`/conversations/${conversationId}/messages`, {
        role: payload.role ?? "user",
        content: payload.content,
        context_sources: payload.context_sources,
      })
      return messageSchema.parse(response.data)
    },
  )
}

export type AssistantStreamEvent = {
  type: string
  conversation_id: number
  assistant_message_id?: number
  stage?: string
}

export function subscribeToAssistantStream(
  conversationId: number,
  onEvent: (event: AssistantStreamEvent) => void,
  onError?: (error: Event | null) => void,
) {
  if (!env.NEXT_PUBLIC_API_URL || typeof window === "undefined") {
    return () => {}
  }
  const url = new URL(`/conversations/${conversationId}/messages/stream`, env.NEXT_PUBLIC_API_URL)
  const source = new EventSource(url.toString())

  const handleEvent = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      onEvent({ type: event.type || data.type || "message", ...data })
    } catch (error) {
      console.error("Failed to parse assistant stream event", error)
    }
  }

  source.addEventListener("status", handleEvent)
  source.addEventListener("completed", handleEvent)
  source.addEventListener("message", handleEvent)
  source.onerror = (event) => {
    console.warn("Assistant stream error", event)
    onError?.(event)
  }

  return () => {
    source.close()
  }
}
