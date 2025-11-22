import { api } from "./client"
import { withMock, mockConversations } from "./mocks"
import { conversationSchema } from "./schemas/conversation"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { Conversation } from "./types"

export async function fetchConversations(): Promise<Conversation[]> {
  return withMock(
    mockConversations,
    async () => {
      const response = await api.get("/conversations", { params: { sorts: "created_at:desc" } })
      const paginatedSchema = paginatedResponseSchema(conversationSchema)
      const parsed = paginatedSchema.parse(response.data)
      return parsed.items
    },
  )
}

export async function fetchConversation(id: number): Promise<Conversation> {
  return withMock(
    mockConversations.find((c) => c.id === id) ?? mockConversations[0],
    async () => {
      const response = await api.get<Conversation>(`/conversations/${id}`)
      return conversationSchema.parse(response.data)
    },
  )
}

export async function createConversation(payload: { title?: string; document_id?: number | null }): Promise<Conversation> {
  return withMock(
    (() => {
      const nextId = Math.max(...mockConversations.map((c) => c.id)) + 1
      const now = new Date().toISOString()
      const created = { id: nextId, title: payload.title ?? "New Conversation", document_id: payload.document_id ?? null, created_at: now }
      mockConversations.unshift(created)
      return created
    })(),
    async () => {
      const response = await api.post<Conversation>("/conversations", payload)
      return conversationSchema.parse(response.data)
    },
  )
}

export async function fetchDocumentConversations(documentId: number): Promise<Conversation[]> {
  return withMock(
    mockConversations.filter((c) => c.document_id === documentId),
    async () => {
      const response = await api.get(`/documents/${documentId}/conversations`)
      const paginatedSchema = paginatedResponseSchema(conversationSchema)
      const parsed = paginatedSchema.parse(response.data)
      return parsed.items
    },
  )
}

export async function createDocumentConversation(documentId: number, payload: { title?: string | null }): Promise<Conversation> {
  return withMock(
    (() => {
      const nextId = Math.max(...mockConversations.map((c) => c.id)) + 1
      const now = new Date().toISOString()
      const created = { id: nextId, title: payload.title ?? "New Conversation", document_id: documentId, created_at: now }
      mockConversations.unshift(created)
      return created
    })(),
    async () => {
      const response = await api.post(`/documents/${documentId}/conversations`, payload)
      return conversationSchema.parse(response.data)
    },
  )
}
