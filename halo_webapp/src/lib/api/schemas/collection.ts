import { z } from "zod"

export const collectionSchema = z
  .object({
    id: z.number(),
    organization_id: z.number().optional(),
    organizationId: z.number().optional(),
    type: z.string(),
    platform: z.string(),
    name: z.string(),
    external_id: z.string().optional(),
    externalId: z.string().optional(),
    description: z.string().nullable().optional(),
    collection_url: z.string().nullable().optional(),
    collectionUrl: z.string().nullable().optional(),
    last_synced_at: z.string().nullable().optional(),
    lastSyncedAt: z.string().nullable().optional(),
    created_at: z.string().optional(),
    createdAt: z.string().optional(),
    updated_at: z.string().optional(),
    updatedAt: z.string().optional(),
  })
  .transform((data) => ({
    id: data.id,
    organization_id: data.organizationId || data.organization_id || 0,
    type: data.type,
    platform: data.platform,
    name: data.name,
    external_id: data.externalId || data.external_id || "",
    description: data.description,
    collection_url: data.collectionUrl || data.collection_url || null,
    last_synced_at: data.lastSyncedAt || data.last_synced_at || null,
    created_at: data.createdAt || data.created_at || "",
    updated_at: data.updatedAt || data.updated_at || "",
  }))

export type Collection = z.infer<typeof collectionSchema>
