import { api } from "./client"
import { withMock, mockCitations } from "./mocks"
import { backendCitationSchema } from "./schemas/citation"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { Citation } from "./types"

export async function fetchCitations(documentId: number): Promise<Citation[]> {
  return withMock(
    mockCitations.filter((c) => c.document_id === documentId),
    async () => {
      const response = await api.get(`/documents/${documentId}/citations`)
      const paginatedSchema = paginatedResponseSchema(backendCitationSchema)
      const parsed = paginatedSchema.parse(response.data)
      return parsed.items.map(mapBackendCitation)
    },
  )
}

export async function createCitation(documentId: number, payload: Omit<Citation, "id" | "document_id">): Promise<Citation> {
  return withMock(
    (() => {
      const nextId = Math.max(0, ...mockCitations.map((c) => c.id ?? 0)) + 1
      const created: Citation = { ...payload, id: nextId, document_id: documentId }
      mockCitations.push(created)
      return created
    })(),
    async () => {
      const response = await api.post(`/documents/${documentId}/citations`, toBackendCitationPayload(payload))
      const parsed = backendCitationSchema.parse(response.data)
      return mapBackendCitation(parsed)
    },
  )
}

function mapBackendCitation(data: any): Citation {
  return {
    id: data.id,
    document_id: data.document_id,
    content_id: data.content_id,
    marker: data.citation_number ?? data.marker,
    position: data.position_in_doc ?? data.position,
    section_index: data.section_index,
    created_at: data.created_at,
  }
}

function toBackendCitationPayload(payload: Omit<Citation, "id" | "document_id">) {
  return {
    content_id: payload.content_id,
    citation_number: payload.marker,
    position_in_doc: payload.position,
    section_index: payload.section_index,
  }
}
