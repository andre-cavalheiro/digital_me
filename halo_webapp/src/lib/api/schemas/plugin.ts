import { z } from "zod"

export const pluginDataSourceIdSchema = z.enum(["cloudflare", "namecheap"])

export const pluginSchema = z.object({
  id: z.number(),
  organization_id: z.number(),
  dataSource: pluginDataSourceIdSchema,
  title: z.string(),
  credentials: z.record(z.any()),
  properties: z.record(z.any()),
  created_at: z.string(),
})

export const pluginCreateSchema = z.object({
  data_source: pluginDataSourceIdSchema,
  title: z.string(),
  credentials: z.record(z.any()).optional(),
  properties: z.record(z.any()).optional(),
})

export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number().optional(),
    size: z.number().optional(),
    current_page: z.string().nullable().optional(),
    current_page_backwards: z.string().nullable().optional(),
    previous_page: z.string().nullable().optional(),
    next_page: z.string().nullable().optional(),
  })

export type Plugin = z.infer<typeof pluginSchema>
export type PluginCreate = z.infer<typeof pluginCreateSchema>
