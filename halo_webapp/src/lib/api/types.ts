export interface PaginatedResponse<T> {
  items: T[]
  total?: number
  size?: number
  current_page?: string | null
  current_page_backwards?: string | null
  previous_page?: string | null
  next_page?: string | null
}

export interface User {
  id: number | null | undefined
  name: string
  email: string
  organization_id: number | null | undefined
}

export interface Organization {
  id?: number | null;
  name: string
}

// Documents
export interface Document {
  id: number
  title: string
  created_at?: string
  updated_at?: string
}

export interface DocumentSection {
  id?: number
  document_id: number
  content: string
  order_index: number
  title?: string | null
  word_count?: number
  updated_at?: string
  embedded_content_id?: number | null
}

export type DocumentContent = DocumentSection[]

// Content sources / suggestions
export interface TwitterAuthor {
  id: string
  username: string
  name: string
  profile_image_url: string
  verified: boolean
  verified_type?: string
  description?: string
}

export interface TwitterPlatformMetadata {
  id: string
  text: string
  author: TwitterAuthor
  public_metrics?: {
    like_count: number
    retweet_count: number
    reply_count: number
    quote_count: number
    impression_count: number
    bookmark_count: number
  }
  tweet_url?: string
  is_retweet?: boolean
  is_quote?: boolean
  is_reply?: boolean
  [key: string]: any
}

export interface ContentItem {
  id: number
  title: string
  summary?: string | null
  excerpt?: string | null
  author?: string
  published_at?: string
  source_url?: string
  body?: string
  platform_metadata?: TwitterPlatformMetadata | Record<string, any>
}

export interface ContentSearchParams {
  query: string
  limit?: number
  source_ids?: number[]
  source_group_ids?: number[]
}

// Citations
export interface Citation {
  id?: number
  document_id: number
  content_id: number
  marker: number
  position?: number
  section_index?: number
  created_at?: string
}

// Assistant conversations
export interface Conversation {
  id: number
  title?: string | null
  document_id?: number | null
  created_at?: string
}

export type MessageRole = "user" | "assistant" | "system"

export interface MessageContextSelection {
  text: string
  section_index?: number
  start?: number
  end?: number
}

export interface MessageContext {
  section_ids?: number[]
  content_ids?: number[]
  selection?: MessageContextSelection | null
}

export interface Message {
  id: number
  conversation_id: number
  role: MessageRole
  content: string
  created_at?: string
  status?: "queued" | "running" | "completed" | "failed"
  metadata?: Record<string, any> | null
}

// Editor selection context
export interface SelectionContext {
  text: string
  start: number
  end: number
}


// Plugin/Integration types
export type PluginDataSourceId = "x" | "community_archive"

export interface CapabilityBadge {
  label: string
  supported: boolean
  tooltip: string
}

export interface PluginDataSource {
  id: PluginDataSourceId
  displayName: string
  icon: string
  enabled: boolean
  getCapabilityBadges: () => CapabilityBadge[]
}

export interface Plugin {
  id: number
  organization_id: number
  dataSource: PluginDataSourceId
  title: string
  credentials?: Record<string, any>
  properties?: Record<string, any>
  created_at: string
}

export interface PluginCreate {
  data_source: PluginDataSourceId
  title: string
  credentials?: Record<string, any>
  properties?: Record<string, any>
}

export interface PluginRead {
  id: number
  data_source: string
  title: string
  properties?: Record<string, any>
}
