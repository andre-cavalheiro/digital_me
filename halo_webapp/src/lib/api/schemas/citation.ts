import { z } from "zod"

export const citationSchema = z.object({
  id: z.number().optional(),
  document_id: z.number(),
  content_id: z.number(),
  marker: z.number(),
  position: z.number().optional(),
  created_at: z.string().optional(),
})

export type Citation = z.infer<typeof citationSchema>
