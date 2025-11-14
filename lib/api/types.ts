export interface House {
  id: number
  url: string
  platform: string
  rawPayload: Record<string, any>
  priceMonth: number
  contractStartDate?: string
  contractMinDuration?: string
  city: string
  cityZone: string
  address: string
  postalCode: string
  roomCount?: number
  surfaceArea?: number
  lastUpdatedAt: string
}

export interface HouseSearch {
  id: number
  city: string
  filters: Record<string, any>
  createdAt: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total?: number
  current_page?: string | null
  current_page_backwards?: string | null
  previous_page?: string | null
  next_page?: string | null
}

export interface User {
  id: number
  name: string
  email: string
  organization_id: number
}

export interface Organization {
  id: number
  name: string
  subscriptionId: string
}
