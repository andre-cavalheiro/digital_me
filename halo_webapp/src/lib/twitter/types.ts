/**
 * Twitter API v2 Entity Type Definitions
 *
 * These types represent the entity data returned by the Twitter API v2
 * for tweets, which includes URLs, mentions, and hashtags with their
 * positions in the tweet text.
 */

/**
 * URL entity from Twitter API v2
 * Contains information about links in tweets
 */
export interface TwitterUrlEntity {
  /** Start position of the URL in the tweet text (Unicode code points) */
  start: number
  /** End position of the URL in the tweet text (Unicode code points) */
  end: number
  /** The t.co shortened URL as it appears in the tweet text */
  url: string
  /** The fully expanded URL (where the link actually goes) */
  expanded_url?: string
  /** A display-friendly version of the URL (e.g., "example.com/path") */
  display_url?: string
  /** Title of the linked content (if available) */
  title?: string
  /** Description of the linked content (if available) */
  description?: string
}

/**
 * User mention entity from Twitter API v2
 * Contains information about @mentions in tweets
 */
export interface TwitterMentionEntity {
  /** Start position of the mention in the tweet text (Unicode code points) */
  start: number
  /** End position of the mention in the tweet text (Unicode code points) */
  end: number
  /** The username of the mentioned user (without the @) */
  username: string
  /** The Twitter user ID of the mentioned user */
  id: string
}

/**
 * Hashtag entity from Twitter API v2
 * Contains information about #hashtags in tweets
 */
export interface TwitterHashtagEntity {
  /** Start position of the hashtag in the tweet text (Unicode code points) */
  start: number
  /** End position of the hashtag in the tweet text (Unicode code points) */
  end: number
  /** The hashtag text (without the #) */
  tag: string
}

/**
 * Container for all Twitter entity types
 * This matches the structure of the entities object from Twitter API v2
 */
export interface TwitterEntities {
  /** Array of URL entities found in the tweet */
  urls?: TwitterUrlEntity[]
  /** Array of user mention entities found in the tweet (user_mentions in some contexts, mentions in others) */
  user_mentions?: TwitterMentionEntity[]
  /** Array of user mention entities (alternative field name used in note_tweet and some API responses) */
  mentions?: TwitterMentionEntity[]
  /** Array of hashtag entities found in the tweet */
  hashtags?: TwitterHashtagEntity[]
}
