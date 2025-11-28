"use client"

import { FolderOpen, ExternalLink } from "lucide-react"
import type { CollectionWithContentCount } from "@/lib/api/collections"
import { Button } from "@/components/ui/button"

type CollectionCardProps = {
  collection: CollectionWithContentCount
}

export function CollectionCard({ collection }: CollectionCardProps) {
  const handleExternalLink = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (collection.collection_url) {
      window.open(collection.collection_url, "_blank", "noopener,noreferrer")
    }
  }

  return (
    <article className="group relative h-full rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-sky-200 hover:shadow-md">
        {/* External link button */}
        {collection.collection_url && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
            onClick={handleExternalLink}
            aria-label={`View ${collection.name} on ${collection.platform}`}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        )}

        {/* Icon and header */}
        <div className="mb-3 flex items-start gap-3">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-sky-100">
            <FolderOpen className="h-6 w-6 text-sky-600" />
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-slate-900 line-clamp-2 leading-tight">{collection.name}</h3>
            <p className="mt-0.5 text-xs text-slate-500 capitalize">{collection.type.replace(/_/g, " ")}</p>
          </div>
        </div>

        {/* Description */}
        {collection.description && (
          <p className="mb-3 line-clamp-2 text-sm leading-relaxed text-slate-700">{collection.description}</p>
        )}

        {/* Stats */}
        <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
          <div className="flex gap-4">
            {collection.content_count !== undefined && collection.content_count > 0 && (
              <span>
                <span className="font-medium text-slate-700">{collection.content_count}</span> items
              </span>
            )}
            {collection.last_synced_at && (
              <span title={new Date(collection.last_synced_at).toLocaleString()}>
                Synced {formatRelativeTime(collection.last_synced_at)}
              </span>
            )}
          </div>
          {collection.platform && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium capitalize text-slate-600">
              {collection.platform}
            </span>
          )}
        </div>
      </article>
  )
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  const diffInMinutes = Math.floor(diffInMs / 60000)
  const diffInHours = Math.floor(diffInMinutes / 60)
  const diffInDays = Math.floor(diffInHours / 24)

  if (diffInMinutes < 1) return "just now"
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInHours < 24) return `${diffInHours}h ago`
  if (diffInDays < 7) return `${diffInDays}d ago`
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`

  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}
