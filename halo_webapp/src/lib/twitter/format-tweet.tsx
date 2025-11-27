import React from "react"
import type { TwitterEntities, TwitterUrlEntity, TwitterMentionEntity } from "./types"

/**
 * HTML entity map for decoding common HTML entities in tweet text
 */
const HTML_ENTITIES: Record<string, string> = {
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#39;": "'",
  "&nbsp;": " ",
}

/**
 * Decodes HTML entities in text
 * Handles both named entities (&amp;) and numeric entities (&#39;)
 */
function decodeHtmlEntities(text: string): string {
  let decoded = text

  // Replace named HTML entities
  for (const [entity, char] of Object.entries(HTML_ENTITIES)) {
    decoded = decoded.replace(new RegExp(entity, "g"), char)
  }

  // Replace numeric HTML entities (e.g., &#x27; or &#39;)
  decoded = decoded.replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)))
  decoded = decoded.replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))

  return decoded
}

/**
 * Validates that a URL is safe (http or https only)
 */
function isSafeUrl(url: string): boolean {
  return url.startsWith("http://") || url.startsWith("https://")
}

/**
 * Entity type used internally for processing
 * Combines all entity types with a type discriminator
 */
type ProcessableEntity =
  | { type: "url"; start: number; end: number; data: TwitterUrlEntity }
  | { type: "mention"; start: number; end: number; data: TwitterMentionEntity }

/**
 * Formats tweet text by converting entities to clickable links
 *
 * This function takes raw tweet text and Twitter API entities data,
 * then returns React elements with clickable links for URLs and mentions.
 * Hashtags are left as plain text per user preference.
 *
 * @param text - The tweet text to format
 * @param entities - Optional Twitter entities object containing URLs, mentions, and hashtags
 * @returns React node with formatted text and clickable links
 *
 * @example
 * ```tsx
 * const formatted = formatTweetText(
 *   "Check out https://example.com and follow @user!",
 *   { urls: [...], user_mentions: [...] }
 * )
 * ```
 */
export function formatTweetText(text: string, entities?: TwitterEntities): React.ReactNode {
  // Handle empty or null text
  if (!text) {
    return null
  }

  // Decode HTML entities first
  const decodedText = decodeHtmlEntities(text)

  // If no entities, return plain decoded text
  if (!entities || (!entities.urls?.length && !entities.user_mentions?.length)) {
    return decodedText
  }

  // Collect all processable entities (URLs and mentions, but not hashtags)
  const processableEntities: ProcessableEntity[] = []
  const seenEntities = new Set<string>()

  const addEntity = (signature: string, entity: ProcessableEntity) => {
    if (seenEntities.has(signature)) {
      return
    }
    seenEntities.add(signature)
    processableEntities.push(entity)
  }

  // Add URL entities
  if (entities.urls) {
    for (const url of entities.urls) {
      // Validate entity has required fields and valid indices
      if (
        typeof url.start === "number" &&
        typeof url.end === "number" &&
        url.start >= 0 &&
        url.end <= decodedText.length &&
        url.start < url.end &&
        url.url
      ) {
        const href = url.expanded_url || url.url
        const signature = `url:${url.start}-${url.end}:${href}`

        addEntity(signature, {
          type: "url",
          start: url.start,
          end: url.end,
          data: url,
        })
      }
    }
  }

  // Add mention entities (check both user_mentions and mentions fields)
  const mentions = entities.user_mentions || entities.mentions
  if (mentions) {
    for (const mention of mentions) {
      // Validate entity has required fields and valid indices
      if (
        typeof mention.start === "number" &&
        typeof mention.end === "number" &&
        mention.start >= 0 &&
        mention.end <= decodedText.length &&
        mention.start < mention.end &&
        mention.username
      ) {
        const signature = `mention:${mention.start}-${mention.end}:${mention.username.toLowerCase()}`

        addEntity(signature, {
          type: "mention",
          start: mention.start,
          end: mention.end,
          data: mention,
        })
      }
    }
  }

  // If no valid entities after filtering, return plain text
  if (processableEntities.length === 0) {
    return decodedText
  }

  // Sort entities by start position (descending) to process from end to start
  // This prevents index shifting as we build segments
  processableEntities.sort((a, b) => b.start - a.start)

  // Build segments array (will be reversed at the end)
  const segments: React.ReactNode[] = []
  let lastIndex = decodedText.length

  // Process each entity from end to beginning
  for (let i = 0; i < processableEntities.length; i++) {
    const entity = processableEntities[i]

    // Add plain text after this entity (if any)
    if (entity.end < lastIndex) {
      const textSegment = decodedText.slice(entity.end, lastIndex)
      if (textSegment) {
        segments.push(textSegment)
      }
    }

    // Create link element based on entity type
    if (entity.type === "url") {
      const urlData = entity.data
      const href = urlData.expanded_url || urlData.url
      const displayText = urlData.expanded_url || urlData.url

      // Only create link if URL is safe
      if (isSafeUrl(href)) {
        segments.push(
          <a
            key={`url-${entity.start}-${entity.end}-${href}`}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="break-words text-sky-600 hover:underline"
          >
            {displayText}
          </a>
        )
      } else {
        // If URL is not safe, render as plain text
        segments.push(displayText)
      }
    } else if (entity.type === "mention") {
      const mentionData = entity.data
      const username = mentionData.username
      const href = `https://twitter.com/${username}`

      segments.push(
        <a
          key={`mention-${entity.start}-${entity.end}-${username.toLowerCase()}`}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="break-words text-sky-600 hover:underline"
        >
          @{username}
        </a>
      )
    }

    lastIndex = entity.start
  }

  // Add any remaining text at the beginning
  if (lastIndex > 0) {
    const textSegment = decodedText.slice(0, lastIndex)
    if (textSegment) {
      segments.push(textSegment)
    }
  }

  // Reverse segments since we built from end to start
  segments.reverse()

  // Return as React fragment
  return <>{segments}</>
}
