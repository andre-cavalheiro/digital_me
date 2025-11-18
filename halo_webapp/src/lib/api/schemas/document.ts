import { z } from "zod"

export const documentSchema = z.object({
  id: z.number(),
  title: z.string(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
})

export const documentSectionSchema = z.object({
  id: z.number().optional(),
  document_id: z.number(),
  content: z.string(),
  order_index: z.number(),
  title: z.string().nullable().optional(),
  word_count: z.number().optional(),
  updated_at: z.string().optional(),
})

export const documentContentSchema = z.array(documentSectionSchema)

export type Document = z.infer<typeof documentSchema>
export type DocumentSection = z.infer<typeof documentSectionSchema>
export type DocumentContent = z.infer<typeof documentContentSchema>
