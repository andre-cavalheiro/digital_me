"use client"

import type { ContentItem, TwitterPlatformMetadata } from "@/lib/api"
import { getContentAuthor } from "@/lib/utils/content-author"
import { GenericContentCard } from "./generic"
import { TwitterContentCard } from "./twitter"

type ContentRendererProps = {
  item: ContentItem
}

/**
 * Routes content to the appropriate card based on platform.
 * Priority: author.platform → metadata inference → generic fallback.
 */
export function ContentRenderer({ item }: ContentRendererProps) {
  const author = getContentAuthor(item)
  const platform = author?.platform?.toLowerCase() || inferPlatformFromMetadata(item)
  const metadata = item.platform_metadata as TwitterPlatformMetadata | undefined

  if (isTwitter(platform, metadata) && metadata) {
    return <TwitterContentCard item={item} metadata={metadata} />
  }

  return <GenericContentCard item={item} />
}

function inferPlatformFromMetadata(item: ContentItem): string | null {
  const metadata = item.platform_metadata
  if (!metadata || typeof metadata !== "object") return null

  // Type guard for Twitter metadata structure
  if (
    "author" in metadata &&
    typeof metadata.author === "object" &&
    metadata.author !== null &&
    "username" in metadata.author &&
    "text" in metadata
  ) {
    return "x"
  }

  return null
}

function isTwitter(platform: string | null, metadata: TwitterPlatformMetadata | undefined): boolean {
  if (!metadata) return false
  if (!platform && !metadata) return false
  const lower = platform?.toLowerCase()

  const metadataLooksTwitter =
    !!metadata &&
    typeof metadata === "object" &&
    ("text" in metadata || "note_tweet" in metadata || "author" in metadata)

  return (
    lower === "x" ||
    lower === "twitter" ||
    metadataLooksTwitter
  )
}
