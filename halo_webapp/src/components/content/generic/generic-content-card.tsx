"use client"

import type { ContentItem } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { ContentCardShell, AuthorBadge } from "../shared"
import { getContentAuthor } from "@/lib/utils/content-author"

export type GenericContentCardProps = {
  item: ContentItem
}

/**
 * Platform-agnostic fallback card.
 * Renders gracefully with only id + title; progressively enhances if more data is present.
 */
export function GenericContentCard({ item }: GenericContentCardProps) {
  const author = getContentAuthor(item)
  const externalUrl = item.source_url || getExternalUrl(item.platform_metadata)
  const platform = author?.platform || "unknown"

  const title = item.title || "Untitled"
  const previewText = item.excerpt || item.summary || item.body?.slice(0, 300)

  return (
    <ContentCardShell
      item={item}
      externalUrl={externalUrl || undefined}
      dragTitle={title}
      dragText={previewText || title}
    >
      <div className="flex items-start gap-2 mb-2">
        <h3 className="flex-1 text-base font-semibold leading-tight text-slate-900 line-clamp-2">
          {title}
        </h3>
        {platform !== "unknown" && (
          <Badge variant="outline" className="text-xs flex-shrink-0">
            {platform}
          </Badge>
        )}
      </div>

      {author && (
        <div className="mt-1">
          <AuthorBadge author={author} size="sm" />
        </div>
      )}

      {item.published_at && (
        <p className="mt-1 text-xs text-slate-500">
          {formatDate(item.published_at)}
        </p>
      )}

      {previewText ? (
        <p className="mt-2 text-sm leading-relaxed text-slate-700 line-clamp-3">
          {previewText}
        </p>
      ) : (
        <p className="mt-2 text-sm text-slate-500 italic">
          No preview available
        </p>
      )}
    </ContentCardShell>
  )
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return dateString
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

/**
 * Type guard to safely extract external_url from platform metadata
 */
function getExternalUrl(metadata: unknown): string | undefined {
  if (
    typeof metadata === "object" &&
    metadata !== null &&
    "external_url" in metadata &&
    typeof (metadata as { external_url: unknown }).external_url === "string"
  ) {
    return (metadata as { external_url: string }).external_url
  }
  return undefined
}
