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
  id: number
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
}

// Content sources / suggestions
export interface ContentItem {
  id: number
  title: string
  summary: string
  author?: string
  published_at?: string
  source_url?: string
}

// Citations
export interface Citation {
  id?: number
  document_id: number
  content_id: number
  marker: number
  position?: number
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

export interface Message {
  id: number
  conversation_id: number
  role: MessageRole
  content: string
  created_at?: string
  context_sources?: number[]
}

// Editor selection context
export interface SelectionContext {
  text: string
  start: number
  end: number
}


// Plugin/Integration types
export type PluginDataSourceId = "cloudflare" | "namecheap"

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
  credentials: Record<string, any>
  properties: Record<string, any>
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
