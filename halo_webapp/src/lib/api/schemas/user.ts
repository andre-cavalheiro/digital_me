import { z } from "zod"

export const userSchema = z.object({
  id: z.number().nullish(),
  name: z.string(),
  email: z.string().email(),
  organization_id: z.number().nullish(),
})

export type User = z.infer<typeof userSchema>
