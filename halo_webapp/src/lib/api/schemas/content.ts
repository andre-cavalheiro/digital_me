import { z } from "zod"

export const contentItemSchema = z
  .object({
    id: z.number(),
    title: z.string().nullable().optional(),
    summary: z.string().nullable().optional(),
    excerpt: z.string().nullable().optional(),
    body: z.string().optional(),
    author: z.string().optional(),
    published_at: z.string().optional(),
    source_url: z.string().optional(),
    external_url: z.string().nullable().optional(),
    organization_id: z.number().optional(),
    source_id: z.number().optional(),
    external_id: z.string().optional(),
    synced_at: z.string().optional(),
    platform_metadata: z.record(z.any()).optional(),
    created_at: z.string().optional(),
    updated_at: z.string().optional(),
  })
  .transform((data) => ({
    id: data.id,
    title: data.title || "Untitled",
    summary: data.summary || data.excerpt || data.body?.slice(0, 200),
    excerpt: data.excerpt || data.body?.slice(0, 200),
    author: data.author,
    published_at: data.published_at,
    source_url: data.source_url || data.external_url || undefined,
  }))

export type ContentItem = z.infer<typeof contentItemSchema>
