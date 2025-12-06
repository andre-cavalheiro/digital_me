import type { ContentItem, Author, TwitterPlatformMetadata } from "@/lib/api/types"

/**
 * Get author from content item with fallback to platform_metadata
 *
 * Priority:
 * 1. item.author (from author table) - preferred
 * 2. platform_metadata.author (legacy fallback)
 *
 * @param item - Content item
 * @returns Author object or undefined
 */
export function getContentAuthor(item: ContentItem): Author | undefined {
  // Priority 1: Use author from author table
  if (item.author) {
    return item.author
  }

  // Priority 2: Fallback to platform_metadata for backward compatibility
  const metadata = item.platform_metadata as TwitterPlatformMetadata | undefined
  if (metadata?.author) {
    // Convert TwitterAuthor to Author format
    return {
      id: 0, // Placeholder - no real ID in metadata
      platform: "x",
      external_id: metadata.author.id,
      display_name: metadata.author.name,
      handle: metadata.author.username,
      avatar_url: metadata.author.profile_image_url,
      profile_url: `https://twitter.com/${metadata.author.username}`,
      bio: metadata.author.description || null,
      follower_count: null,
      following_count: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  }

  return undefined
}
