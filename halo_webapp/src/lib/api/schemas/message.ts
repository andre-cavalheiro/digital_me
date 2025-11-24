import { z } from "zod"

export const contextSelectionSchema = z
  .object({
    text: z.string(),
    section_index: z.number().optional(),
    start: z.number().optional(),
    end: z.number().optional(),
  })
  .strict()

export const messageContextSchema = z
  .object({
    section_ids: z.array(z.number()).optional(),
    content_ids: z.array(z.number()).optional(),
    selection: contextSelectionSchema.nullable().optional(),
  })
  .strict()

export const messageSchema = z.object({
  id: z.number(),
  conversation_id: z.number(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  created_at: z.string().optional(),
  context_sources: messageContextSchema.nullable().optional(),
  status: z.enum(["queued", "running", "completed", "failed"]).default("completed"),
  metadata: z.record(z.string(), z.unknown()).nullable().optional(),
})

export type Message = z.infer<typeof messageSchema>
