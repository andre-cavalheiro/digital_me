import { z } from "zod"

export const organizationSchema = z.object({
  id: z.number(),
  name: z.string(),
})

export type Organization = z.infer<typeof organizationSchema>
