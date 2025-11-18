import { api } from "./client"
import { withMock, mockDocumentContents } from "./mocks"
import { documentContentSchema } from "./schemas/document"
import type { DocumentContent, DocumentSection } from "./types"

function sortSections(sections: DocumentSection[]): DocumentSection[] {
  return [...sections].sort((a, b) => a.order_index - b.order_index)
}

export async function fetchDocumentContent(documentId: number): Promise<DocumentContent> {
  return withMock(
    mockDocumentContents[documentId] ?? [],
    async () => {
      const response = await api.get<DocumentContent>(`/documents/${documentId}/content`)
      const withDefaults = response.data.map((section, idx) => ({
        ...section,
        document_id: section.document_id ?? documentId,
        order_index: section.order_index ?? idx,
      }))
      const parsed = documentContentSchema.parse(withDefaults)
      return sortSections(parsed)
    },
  )
}

export async function saveDocumentContent(documentId: number, sections: DocumentSection[]): Promise<DocumentContent> {
  return withMock(
    (() => {
      const normalized = sortSections(
        sections.map((section, idx) => ({
          ...section,
          document_id: documentId,
          order_index: section.order_index ?? idx,
          updated_at: new Date().toISOString(),
        })),
      )
      mockDocumentContents[documentId] = normalized
      return normalized
    })(),
    async () => {
      const payload = {
        sections: sections.map((section, idx) => ({
          content: section.content,
          order_index: section.order_index ?? idx,
          title: section.title,
          word_count: section.word_count,
        })),
      }
      const response = await api.put<DocumentContent>(`/documents/${documentId}/content`, payload)
      const withDefaults = response.data.map((section, idx) => ({
        ...section,
        document_id: section.document_id ?? documentId,
        order_index: section.order_index ?? idx,
      }))
      const parsed = documentContentSchema.parse(withDefaults)
      return sortSections(parsed)
    },
  )
}
