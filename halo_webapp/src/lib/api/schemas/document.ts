import { z } from "zod"

export const documentSchema = z
  .object({
    id: z.number(),
    title: z.string(),
    created_at: z.string().optional(),
    createdAt: z.string().optional(),
    updated_at: z.string().optional(),
    updatedAt: z.string().optional(),
  })
  .transform((data) => ({
    id: data.id,
    title: data.title,
    created_at: data.created_at ?? data.createdAt,
    updated_at: data.updated_at ?? data.updatedAt,
  }))

export const documentSectionSchema = z
  .object({
    id: z.number().optional(),
    document_id: z.number().optional(),
    documentId: z.number().optional(),
    content: z.string().optional(),
    order_index: z.number().optional(),
    orderIndex: z.number().optional(),
    title: z.string().nullable().optional(),
    word_count: z.number().nullable().optional(),
    wordCount: z.number().nullable().optional(),
    updated_at: z.string().optional(),
    updatedAt: z.string().optional(),
    embedded_content_id: z.number().nullable().optional(),
    embeddedContentId: z.number().nullable().optional(),
  })
  .transform((data) => ({
    id: data.id,
    document_id: data.document_id ?? data.documentId ?? 0,
    content: data.content ?? "",
    order_index: data.order_index ?? data.orderIndex ?? 0,
    title: data.title ?? null,
    word_count: data.word_count ?? data.wordCount ?? undefined,
    updated_at: data.updated_at ?? data.updatedAt,
    embedded_content_id: data.embedded_content_id ?? data.embeddedContentId ?? null,
  }))

export const documentContentSchema = z.array(documentSectionSchema)

export type Document = z.infer<typeof documentSchema>
export type DocumentSection = z.infer<typeof documentSectionSchema>
export type DocumentContent = z.infer<typeof documentContentSchema>
