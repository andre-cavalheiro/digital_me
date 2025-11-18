import { api } from "./client"
import { withMock, mockDocumentContents } from "./mocks"
import { documentContentSchema } from "./schemas/document"
import type { DocumentContent, DocumentSection } from "./types"

export async function fetchDocumentContent(documentId: number): Promise<DocumentContent> {
  return withMock(
    mockDocumentContents[documentId] ?? [],
    async () => {
      const response = await api.get<DocumentContent>(`/documents/${documentId}/content`)
      return documentContentSchema.parse(response.data)
    },
  )
}

export async function saveDocumentContent(
  documentId: number,
  sections: DocumentSection[],
): Promise<DocumentContent> {
  return withMock(
    (() => {
      const normalized = sections.map((section, idx) => ({
        ...section,
        document_id: documentId,
        order_index: idx,
        updated_at: new Date().toISOString(),
      }))
      mockDocumentContents[documentId] = normalized
      return normalized
    })(),
    async () => {
      const payload = { sections }
      const response = await api.put<DocumentContent>(`/documents/${documentId}/content`, payload)
      return documentContentSchema.parse(response.data)
    },
  )
}
