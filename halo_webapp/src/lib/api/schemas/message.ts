import { z } from "zod"

export const messageSchema = z.object({
  id: z.number(),
  conversation_id: z.number(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  created_at: z.string().optional(),
  context_sources: z.array(z.number()).optional(),
  status: z.enum(["queued", "running", "completed", "failed"]).default("completed"),
  metadata: z.record(z.string(), z.unknown()).nullable().optional(),
})

export type Message = z.infer<typeof messageSchema>
