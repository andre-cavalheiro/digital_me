"use client"

import Image from "next/image"
import { ExternalLink, User } from "lucide-react"
import type { AuthorWithContentCount } from "@/lib/api/authors"
import { Button } from "@/components/ui/button"

type AuthorCardProps = {
  author: AuthorWithContentCount
}

export function AuthorCard({ author }: AuthorCardProps) {
  const handleExternalLink = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (author.profile_url) {
      window.open(author.profile_url, "_blank", "noopener,noreferrer")
    }
  }

  return (
    <article className="group relative h-full rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-sky-200 hover:shadow-md">
        {/* External link button */}
        {author.profile_url && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
            onClick={handleExternalLink}
            aria-label={`View ${author.display_name} on ${author.platform}`}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        )}

        {/* Avatar and header */}
        <div className="mb-3 flex items-start gap-3">
          <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-full bg-slate-200">
            {author.avatar_url ? (
              <Image
                src={author.avatar_url}
                alt={author.display_name}
                fill
                className="object-cover"
                unoptimized
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center">
                <User className="h-6 w-6 text-slate-400" />
              </div>
            )}
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-semibold text-slate-900">{author.display_name}</h3>
            <p className="truncate text-sm text-slate-500">{author.handle}</p>
          </div>
        </div>

        {/* Bio */}
        {author.bio && (
          <p className="mb-3 line-clamp-2 text-sm leading-relaxed text-slate-700">{author.bio}</p>
        )}

        {/* Stats */}
        <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
          <div className="flex gap-4">
            {author.follower_count !== null && author.follower_count !== undefined && (
              <span>
                <span className="font-medium text-slate-700">{formatNumber(author.follower_count)}</span> followers
              </span>
            )}
            {author.content_count !== undefined && author.content_count > 0 && (
              <span>
                <span className="font-medium text-slate-700">{formatNumber(author.content_count)}</span> items
              </span>
            )}
          </div>
          {author.platform && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium capitalize text-slate-600">
              {author.platform}
            </span>
          )}
        </div>
      </article>
  )
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}
