"use client"

import { useState } from "react"
import type { ContentItem, TwitterPlatformMetadata } from "@/lib/api"
import { formatTweetText } from "@/lib/twitter/format-tweet"
import { getContentAuthor } from "@/lib/utils/content-author"
import { ContentCardShell, AuthorBadge, MetricsDisplay } from "../shared"
import { QuotedTweet } from "./quoted-tweet"
import { MediaGallery } from "./media-gallery"

export type TwitterContentCardProps = {
  item: ContentItem
  metadata: TwitterPlatformMetadata
}

const TWEET_COLLAPSE_THRESHOLD = 280 // Characters before showing "Show more"

/**
 * Twitter-specific content card with platform enhancements
 * - Tweet text formatting with entities
 * - Verification badge
 * - Public metrics (likes, retweets, replies)
 * - Quoted tweet display
 * - Long tweet expansion
 */
export function TwitterContentCard({ item, metadata }: TwitterContentCardProps) {
  const author = getContentAuthor(item)

  // Safety check - if no author, don't render
  if (!author) {
    console.warn("[TwitterContentCard] No author found for content:", item.id)
    return null
  }

  const tweetText = metadata.note_tweet?.text || item.body || metadata.text
  const entities = metadata.note_tweet?.entities || metadata.entities
  const tweetUrl = metadata.tweet_url || `https://twitter.com/${author.handle}/status/${metadata.id}`

  const [isExpanded, setIsExpanded] = useState(false)
  const isLongTweet = tweetText.length > TWEET_COLLAPSE_THRESHOLD

  return (
    <ContentCardShell
      item={item}
      externalUrl={tweetUrl}
      dragTitle={`@${author.handle}`}
      dragText={tweetText}
    >
      <AuthorBadge author={author}>
        {metadata.author?.verified && (
          <svg className="h-4 w-4 flex-shrink-0 text-sky-500" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z" />
          </svg>
        )}
      </AuthorBadge>

      <div className="mt-2">
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

      {metadata.media && metadata.media.length > 0 && (
        <MediaGallery media={metadata.media} />
      )}

      {item.extra_fields?.quoted_tweet && (
        <QuotedTweet quotedTweet={item.extra_fields.quoted_tweet} />
      )}

      {metadata.public_metrics && (
        <div className="mt-2">
          <MetricsDisplay
            metrics={[
              { label: "likes", value: metadata.public_metrics.like_count },
              { label: "retweets", value: metadata.public_metrics.retweet_count },
              { label: "replies", value: metadata.public_metrics.reply_count },
            ]}
          />
        </div>
      )}
    </ContentCardShell>
  )
}

// Legacy export for backward compatibility during migration
export { TwitterContentCard as TweetCard }
