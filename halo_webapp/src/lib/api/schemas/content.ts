import { z } from "zod"

export const contentItemSchema = z.object({
  id: z.number(),
  title: z.string(),
  summary: z.string(),
  author: z.string().optional(),
  published_at: z.string().optional(),
  source_url: z.string().url().optional(),
})

export type ContentItem = z.infer<typeof contentItemSchema>
