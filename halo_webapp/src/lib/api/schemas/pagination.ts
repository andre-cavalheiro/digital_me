import { z } from "zod"

export function paginatedResponseSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    total: z.number().nullable(),
    current_page: z.string().nullable(),
    current_page_backwards: z.string().nullable(),
    previous_page: z.string().nullable(),
    next_page: z.string().nullable(),
  })
}

export type PaginatedResponse<T> = {
  items: T[]
  total: number | null
  current_page: string | null
  current_page_backwards: string | null
  previous_page: string | null
  next_page: string | null
}
