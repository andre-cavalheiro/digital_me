import { z } from "zod"

export const contentItemSchema = z
  .object({
    id: z.number(),
    title: z.string().nullable().optional(),
    summary: z.string().nullable().optional(),
    excerpt: z.string().nullable().optional(),
    body: z.string().optional(),
    author: z.string().optional(),
    author_id: z.number().nullable().optional(),
    authorId: z.number().nullable().optional(),
    published_at: z.string().optional(),
    publishedAt: z.string().optional(),
    source_url: z.string().optional(),
    external_url: z.string().nullable().optional(),
    externalUrl: z.string().nullable().optional(),
    organization_id: z.number().optional(),
    organizationId: z.number().optional(),
    external_id: z.string().optional(),
    externalId: z.string().optional(),
    synced_at: z.string().optional(),
    syncedAt: z.string().optional(),
    platform_metadata: z.record(z.string(), z.unknown()).optional(),
    platformMetadata: z.record(z.string(), z.unknown()).optional(),
    created_at: z.string().optional(),
    createdAt: z.string().optional(),
    updated_at: z.string().optional(),
    updatedAt: z.string().optional(),
  })
  .transform((data) => ({
    id: data.id,
    title: data.title || "Untitled",
    summary: data.summary || data.excerpt || data.body?.slice(0, 200),
    excerpt: data.excerpt || data.body?.slice(0, 200),
    author: data.author,
    author_id: data.author_id ?? data.authorId ?? null,
    published_at: data.published_at || data.publishedAt,
    source_url: data.source_url || data.source_url || data.external_url || data.externalUrl || undefined,
    platform_metadata: data.platformMetadata || data.platform_metadata,
    body: data.body,
  }))

export type ContentItem = z.infer<typeof contentItemSchema>
