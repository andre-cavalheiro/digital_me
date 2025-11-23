import { z } from "zod"

const backendCitationSchemaRaw = z.object({
  // snake_case fields
  id: z.number().optional(),
  document_id: z.number().optional(),
  content_id: z.number().optional(),
  citation_number: z.number().optional(),
  position_in_doc: z.number().optional().nullable(),
  section_index: z.number().optional().nullable(),
  created_at: z.string().optional(),
  marker: z.number().optional(),
  position: z.number().optional().nullable(),
  // camelCase fields returned by the API serializers
  documentId: z.number().optional(),
  contentId: z.number().optional(),
  sectionIndex: z.number().optional().nullable(),
  createdAt: z.string().optional(),
})

export const backendCitationSchema = backendCitationSchemaRaw.transform(
  (data) => {
    const document_id = data.document_id ?? data.documentId
    const content_id = data.content_id ?? data.contentId
    const position_in_doc = data.position_in_doc ?? data.position
    const section_index = data.section_index ?? data.sectionIndex

    return {
      id: data.id,
      document_id,
      content_id,
      citation_number: data.citation_number ?? data.marker,
      marker: data.marker ?? data.citation_number,
      position_in_doc,
      position: position_in_doc,
      section_index,
      created_at: data.created_at ?? data.createdAt,
    }
  },
)

export type BackendCitation = z.infer<typeof backendCitationSchema>
