import { z } from "zod"

export const authorSchema = z
  .object({
    id: z.number(),
    platform: z.string(),
    external_id: z.string().optional(),
    externalId: z.string().optional(),
    display_name: z.string().optional(),
    displayName: z.string().optional(),
    handle: z.string(),
    avatar_url: z.string().optional(),
    avatarUrl: z.string().optional(),
    profile_url: z.string().optional(),
    profileUrl: z.string().optional(),
    bio: z.string().nullable().optional(),
    follower_count: z.number().nullable().optional(),
    followerCount: z.number().nullable().optional(),
    following_count: z.number().nullable().optional(),
    followingCount: z.number().nullable().optional(),
    created_at: z.string().optional(),
    createdAt: z.string().optional(),
    updated_at: z.string().optional(),
    updatedAt: z.string().optional(),
  })
  .transform((data) => ({
    id: data.id,
    platform: data.platform,
    external_id: data.externalId || data.external_id || "",
    display_name: data.displayName || data.display_name || "",
    handle: data.handle,
    avatar_url: data.avatarUrl || data.avatar_url || "",
    profile_url: data.profileUrl || data.profile_url || "",
    bio: data.bio,
    follower_count: data.followerCount ?? data.follower_count ?? null,
    following_count: data.followingCount ?? data.following_count ?? null,
    created_at: data.createdAt || data.created_at || "",
    updated_at: data.updatedAt || data.updated_at || "",
  }))

export type Author = z.infer<typeof authorSchema>
