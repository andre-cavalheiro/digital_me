import { z } from "zod"

export const pluginDataSourceIdSchema = z.enum(["x", "community_archive"])

// Allow both camelCase (API responses) and snake_case (internal) and normalize to snake_case
const pluginSchemaRaw = z.object({
  id: z.number(),
  organization_id: z.number().optional(),
  organizationId: z.number().optional(),
  dataSource: pluginDataSourceIdSchema,
  title: z.string(),
  credentials: z.record(z.string(), z.unknown()).optional(),
  properties: z.record(z.string(), z.unknown()).optional(),
  created_at: z.string().optional(),
  createdAt: z.string().optional(),
})

export const pluginSchema = pluginSchemaRaw.transform((data) => {
  const organization_id = data.organization_id ?? data.organizationId
  const created_at = data.created_at ?? data.createdAt

  if (organization_id === undefined) {
    throw new Error("Missing organization_id")
  }
  if (created_at === undefined) {
    throw new Error("Missing created_at")
  }

  return {
    id: data.id,
    organization_id,
    dataSource: data.dataSource,
    title: data.title,
    credentials: data.credentials,
    properties: data.properties,
    created_at,
  }
})

export const pluginCreateSchema = z.object({
  data_source: pluginDataSourceIdSchema,
  title: z.string(),
  credentials: z.record(z.string(), z.unknown()).optional(),
  properties: z.record(z.string(), z.unknown()).optional(),
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
