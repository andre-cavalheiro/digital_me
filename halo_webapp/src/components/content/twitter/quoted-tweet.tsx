"use client"

import Image from "next/image"
import type { QuotedTweetData } from "@/lib/api"
import { MediaGallery } from "./media-gallery"

export type QuotedTweetProps = {
  quotedTweet: QuotedTweetData
}

/**
 * Displays a quoted tweet within a tweet card
 */
export function QuotedTweet({ quotedTweet }: QuotedTweetProps) {
  const { author, text, url, media } = quotedTweet

  const handleQuotedTweetClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer")
    }
  }

  return (
    <div
      className="mt-2 cursor-pointer rounded-lg border border-slate-300 p-3 transition hover:bg-slate-50"
      onClick={handleQuotedTweetClick}
    >
      {author && (
        <div className="mb-2 flex items-center gap-2">
          <div className="relative h-5 w-5 overflow-hidden rounded-full bg-slate-200">
            <Image
              src={author.avatar_url}
              alt={author.name}
              fill
              className="object-cover"
              unoptimized
            />
          </div>
          <div className="flex min-w-0 items-center gap-1">
            <span className="truncate text-xs font-semibold text-slate-900">{author.name}</span>
            <span className="truncate text-xs text-slate-500">@{author.username}</span>
          </div>
        </div>
      )}
      <p className="whitespace-pre-wrap break-words text-xs leading-relaxed text-slate-700">
        {text}
      </p>
      {media && media.length > 0 && (
        <MediaGallery media={media} compact />
      )}
    </div>
  )
}
