"use client"

import { useState } from "react"
import Image from "next/image"
import { ExternalLink } from "lucide-react"
import type { ContentItem, TwitterPlatformMetadata } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { formatTweetText } from "@/lib/twitter/format-tweet"

type TweetCardProps = {
  item: ContentItem
  metadata: TwitterPlatformMetadata
}

const TWEET_COLLAPSE_THRESHOLD = 280 // Characters before showing "Show more"

export function TweetCard({ item, metadata }: TweetCardProps) {
  const { author } = metadata
  const tweetText = metadata.note_tweet?.text || item.body || metadata.text
  const entities = metadata.note_tweet?.entities || metadata.entities
  const tweetUrl = metadata.tweet_url || `https://twitter.com/${author.username}/status/${metadata.id}`

  const [isExpanded, setIsExpanded] = useState(false)
  const isLongTweet = tweetText.length > TWEET_COLLAPSE_THRESHOLD

  const handleExternalLink = (e: React.MouseEvent) => {
    e.stopPropagation()
    window.open(tweetUrl, "_blank", "noopener,noreferrer")
  }

  return (
    <article
      draggable
      className="group relative cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md active:cursor-grabbing"
      onDragStart={(event) => {
        event.dataTransfer?.setData("application/x-content-id", String(item.id))
        event.dataTransfer?.setData("application/x-content-title", `@${author.username}`)
        event.dataTransfer?.setData("text/plain", tweetText)
        event.dataTransfer?.setDragImage(createDragImage(`@${author.username}`), 0, 0)
      }}
    >
      {/* External link button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-2 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
        onClick={handleExternalLink}
        aria-label="Open tweet in new tab"
      >
        <ExternalLink className="h-4 w-4" />
      </Button>

      <div className="flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="relative h-10 w-10 overflow-hidden rounded-full bg-slate-200">
            <Image
              src={author.profile_image_url}
              alt={author.name}
              fill
              className="object-cover"
              unoptimized
            />
          </div>
        </div>

        {/* Tweet content */}
        <div className="min-w-0 flex-1 overflow-hidden">
          {/* Author info */}
          <div className="flex items-start gap-1">
            <span className="truncate font-semibold text-sm leading-tight text-slate-900">
              {author.name}
            </span>
            {author.verified && (
              <svg className="h-4 w-4 flex-shrink-0 text-sky-500" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z" />
              </svg>
            )}
            <span className="truncate text-sm text-slate-500">@{author.username}</span>
          </div>

          {/* Tweet text */}
          <div className="mt-1">
            <p
              className={`whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-900 ${
                isLongTweet && !isExpanded ? "line-clamp-4" : ""
              }`}
            >
              {formatTweetText(tweetText, entities)}
            </p>
            {isLongTweet && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setIsExpanded(!isExpanded)
                }}
                className="mt-1 text-xs font-medium text-sky-600 hover:text-sky-700 hover:underline"
              >
                {isExpanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>

          {/* Metrics */}
          {metadata.public_metrics && (
            <div className="mt-2 flex gap-4 text-xs text-slate-500">
              {metadata.public_metrics.like_count > 0 && (
                <span>{metadata.public_metrics.like_count.toLocaleString()} likes</span>
              )}
              {metadata.public_metrics.retweet_count > 0 && (
                <span>{metadata.public_metrics.retweet_count.toLocaleString()} retweets</span>
              )}
              {metadata.public_metrics.reply_count > 0 && (
                <span>{metadata.public_metrics.reply_count.toLocaleString()} replies</span>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

type SourceCardProps = {
  item: ContentItem
}

export function SourceCard({ item }: SourceCardProps) {
  const externalUrl = item.source_url || item.platform_metadata?.external_url

  const handleExternalLink = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (externalUrl) {
      window.open(externalUrl, "_blank", "noopener,noreferrer")
    }
  }

  return (
    <article
      draggable
      className="group relative rounded-lg border border-slate-200 bg-white/80 p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md"
      onDragStart={(event) => {
        event.dataTransfer?.setData("application/x-content-id", String(item.id))
        event.dataTransfer?.setData("application/x-content-title", item.title)
        event.dataTransfer?.setData("text/plain", item.title)
        event.dataTransfer?.setDragImage(createDragImage(item.title), 0, 0)
      }}
    >
      {/* External link button */}
      {externalUrl && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
          onClick={handleExternalLink}
          aria-label="Open article in new tab"
        >
          <ExternalLink className="h-4 w-4" />
        </Button>
      )}

      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <p className="text-sm font-medium leading-5">{item.title}</p>
          {(item.author || item.published_at) && (
            <p className="text-xs text-muted-foreground">
              {[item.author, item.published_at ? formatDate(item.published_at) : undefined]
                .filter(Boolean)
                .join(" • ")}
            </p>
          )}
        </div>
      </div>
      <p className="mt-2 line-clamp-3 text-sm leading-6 text-muted-foreground">
        {item.excerpt || item.summary || "No excerpt available."}
      </p>
    </article>
  )
}

// Helper functions
function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

function createDragImage(title: string) {
  const el = document.createElement("div")
  el.textContent = `Source: ${title}`
  el.style.position = "fixed"
  el.style.top = "0"
  el.style.left = "0"
  el.style.padding = "6px 10px"
  el.style.borderRadius = "8px"
  el.style.background = "rgba(12,74,110,0.9)"
  el.style.color = "white"
  el.style.fontSize = "12px"
  el.style.fontWeight = "600"
  el.style.pointerEvents = "none"
  document.body.appendChild(el)
  setTimeout(() => {
    if (el.parentNode) {
      el.parentNode.removeChild(el)
    }
  }, 0)
  return el
}
