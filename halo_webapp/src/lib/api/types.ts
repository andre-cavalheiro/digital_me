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
