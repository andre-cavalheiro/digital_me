import { api } from "./client"
import { withMock, mockCitations } from "./mocks"
import { citationSchema } from "./schemas/citation"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { Citation } from "./types"

export async function fetchCitations(documentId: number): Promise<Citation[]> {
  return withMock(
    mockCitations.filter((c) => c.document_id === documentId),
    async () => {
      const response = await api.get(`/documents/${documentId}/citations`)
      const paginatedSchema = paginatedResponseSchema(citationSchema)
      const parsed = paginatedSchema.parse(response.data)
      return parsed.items
    },
  )
}

export async function createCitation(documentId: number, payload: Omit<Citation, "id" | "document_id">): Promise<Citation> {
  return withMock(
    (() => {
      const nextId = Math.max(0, ...mockCitations.map((c) => c.id ?? 0)) + 1
      const created = { ...payload, id: nextId, document_id: documentId }
      mockCitations.push(created)
      return created
    })(),
    async () => {
      const response = await api.post<Citation>(`/documents/${documentId}/citations`, payload)
      return citationSchema.parse(response.data)
    },
  )
}
