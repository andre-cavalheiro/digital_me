import { z } from "zod"

export const conversationSchema = z.object({
  id: z.number(),
  title: z.string().nullable().optional(),
  document_id: z.number().nullable().optional(),
  created_at: z.string().optional(),
})

export type Conversation = z.infer<typeof conversationSchema>
