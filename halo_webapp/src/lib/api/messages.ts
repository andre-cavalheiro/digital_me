import { api } from "./client"
import { withMock, mockMessages } from "./mocks"
import { messageSchema } from "./schemas/message"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { Message, MessageRole } from "./types"

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

export async function sendMessage(conversationId: number, payload: { content: string; role?: MessageRole; context_sources?: number[] }): Promise<Message> {
  return withMock(
    (() => {
      const nextId = Math.max(...mockMessages.map((m) => m.id)) + 1
      const created: Message = {
        id: nextId,
        conversation_id: conversationId,
        role: payload.role ?? "user",
        content: payload.content,
        context_sources: payload.context_sources,
        created_at: new Date().toISOString(),
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
