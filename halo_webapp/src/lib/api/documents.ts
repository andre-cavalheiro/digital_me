import { api } from "./client"
import { withMock, mockDocuments } from "./mocks"
import { documentSchema } from "./schemas/document"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { Document } from "./types"

export async function fetchDocuments(): Promise<Document[]> {
  return withMock(mockDocuments, async () => {
    const response = await api.get("/documents")
    const paginatedSchema = paginatedResponseSchema(documentSchema)
    const parsed = paginatedSchema.parse(response.data)
    return parsed.items
  })
}

export async function fetchDocument(id: number): Promise<Document> {
  return withMock(
    mockDocuments.find((doc) => doc.id === id) ?? mockDocuments[0],
    async () => {
      const response = await api.get<Document>(`/documents/${id}`)
      return documentSchema.parse(response.data)
    },
  )
}

export async function createDocument(payload: { title?: string }): Promise<Document> {
  return withMock(
    (() => {
      const nextId = Math.max(...mockDocuments.map((d) => d.id)) + 1
      const title = payload.title?.trim() || "Untitled Document"
      const now = new Date().toISOString()
      const created = { id: nextId, title, created_at: now, updated_at: now }
      mockDocuments.unshift(created)
      return created
    })(),
    async () => {
      const title = payload.title?.trim() || "Untitled Document"
      const response = await api.post<Document>("/documents", { title })
      return documentSchema.parse(response.data)
    },
  )
}

export async function updateDocumentTitle(id: number, title: string): Promise<Document> {
  return withMock(
    (() => {
      const index = mockDocuments.findIndex((doc) => doc.id === id)
      if (index >= 0) {
        const updated = { ...mockDocuments[index], title, updated_at: new Date().toISOString() }
        mockDocuments[index] = updated
        return updated
      }
      return { id, title }
    })(),
    async () => {
      const response = await api.put<Document>(`/documents/${id}`, { title })
      return documentSchema.parse(response.data)
    },
  )
}
