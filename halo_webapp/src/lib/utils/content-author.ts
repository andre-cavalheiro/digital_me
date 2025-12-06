import type { ContentItem, Author } from "@/lib/api/types"

/**
 * Get author from content item.
 *
 * Author data comes from the author table (via include=author API parameter).
 * The frontend always requests author data, so this should always be populated.
 *
 * @param item - Content item
 * @returns Author object or undefined
 */
export function getContentAuthor(item: ContentItem): Author | undefined {
  return item.author
}
