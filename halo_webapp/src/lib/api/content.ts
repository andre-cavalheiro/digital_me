import { api } from "./client"
import { withMock, mockContentItems } from "./mocks"
import { contentItemSchema } from "./schemas/content"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { ContentItem, ContentSearchParams, FetchContentListParams, ContentListResponse } from "./types"

export async function fetchContentFeed(params?: { limit?: number; sorts?: string; include?: string }): Promise<ContentItem[]> {
  return withMock(
    mockContentItems,
    async () => {
      const response = await api.get("/content", { params: { ...params, include: "author" } })
      const paginatedSchema = paginatedResponseSchema(contentItemSchema)
      const parsed = paginatedSchema.parse(response.data)
      return parsed.items
    },
  )
}

export async function fetchContentItem(id: number): Promise<ContentItem> {
  return withMock(
    mockContentItems.find((item) => item.id === id) ?? mockContentItems[0],
    async () => {
      const response = await api.get<ContentItem>(`/content/${id}`, { params: { include: "author" } })
      return contentItemSchema.parse(response.data)
    },
  )
}

export async function searchContent(params: ContentSearchParams): Promise<ContentItem[]> {
  const payload = {
    query: params.query,
    limit: params.limit ?? 20,
  }

  // Build query parameters for filters
  const queryParams: Record<string, string | string[]> = {
    include: "author",
  }
  const filters: string[] = []

  if (params.authorIds && params.authorIds.length > 0) {
    filters.push(`author_id:in:${params.authorIds.join(",")}`)
  }

  if (params.collectionIds && params.collectionIds.length > 0) {
    filters.push(`collection_id:in:${params.collectionIds.join(",")}`)
  }

  if (filters.length > 0) {
    queryParams.filters = filters

    // Use OR logic when filtering by multiple criteria (author + collections)
    // This returns content that matches ANY of the filter conditions
    if (filters.length > 1) {
      queryParams.filter_logic = "or"
    }
  }

  return withMock(
    rankMockContent(payload.query, payload.limit ?? 20),
    async () => {
      const response = await api.post(`/content/search`, payload, { params: queryParams })
      const paginatedSchema = paginatedResponseSchema(contentItemSchema)
      const parsedPaginated = paginatedSchema.safeParse(response.data)
      if (parsedPaginated.success) {
        return parsedPaginated.data.items
      }
      const parsedArray = contentItemSchema.array().safeParse(response.data)
      if (parsedArray.success) {
        return parsedArray.data
      }

      if (Array.isArray(response.data)) {
        const normalized = response.data
          .map((item, idx) => normalizeContentItem(item, idx))
          .filter(Boolean) as ContentItem[]
        if (normalized.length) {
          return normalized
        }
      }

      return rankMockContent(payload.query, payload.limit ?? 20)
    },
  )
}

function rankMockContent(query: string, limit: number): ContentItem[] {
  const normalizedQuery = query.toLowerCase()
  const terms = normalizedQuery
    .split(/\s+/)
    .map((word) => word.replace(/[^\w]/g, ""))
    .filter(Boolean)

  const scored = mockContentItems
    .map((item) => {
      const haystack = `${item.title} ${item.excerpt ?? item.summary ?? ""}`.toLowerCase()
      const score = terms.reduce((total, term) => (haystack.includes(term) ? total + 1 : total), 0)
      return { item, score }
    })
    .filter(({ score }) => score > 0 || !terms.length)

  return scored
    .sort((a, b) => b.score - a.score || a.item.id - b.item.id)
    .slice(0, limit)
    .map(({ item }) => item)
}

function normalizeContentItem(raw: any, idx: number): ContentItem | null {
  if (!raw || typeof raw !== "object") return null
  const id = typeof raw.id === "number" ? raw.id : idx + 1
  const title = typeof raw.title === "string" && raw.title.trim() ? raw.title : "Untitled source"
  const excerpt =
    typeof raw.excerpt === "string" && raw.excerpt.trim()
      ? raw.excerpt
      : typeof raw.summary === "string" && raw.summary.trim()
        ? raw.summary
        : "No excerpt available."

  return {
    id,
    title,
    summary: typeof raw.summary === "string" ? raw.summary : undefined,
    excerpt,
    author: typeof raw.author === "string" ? raw.author : undefined,
    published_at: typeof raw.published_at === "string" ? raw.published_at : undefined,
    source_url: typeof raw.source_url === "string" ? raw.source_url : undefined,
  }
}

export async function fetchContentList(params: FetchContentListParams = {}): Promise<ContentListResponse> {
  const {
    cursor,
    limit = 20,
    authorIds,
    collectionIds,
    publishedAfter,
    publishedBefore,
    sortBy = "published_at",
    sortOrder = "desc",
    includeTotal = false,
  } = params

  // Build query parameters
  const queryParams: Record<string, string | string[]> = {
    size: String(limit),
    include: "author",
  }

  if (cursor) {
    queryParams.cursor = cursor
  }

  if (includeTotal) {
    queryParams.includeTotal = "true"
  }

  // Build filters array
  const filters: string[] = []

  if (authorIds && authorIds.length > 0) {
    if (authorIds.length === 1) {
      filters.push(`author_id:eq:${authorIds[0]}`)
    } else {
      filters.push(`author_id:in:${authorIds.join(",")}`)
    }
  }

  if (collectionIds && collectionIds.length > 0) {
    if (collectionIds.length === 1) {
      filters.push(`collection_id:eq:${collectionIds[0]}`)
    } else {
      filters.push(`collection_id:in:${collectionIds.join(",")}`)
    }
  }

  if (publishedAfter) {
    filters.push(`published_at:gte:${publishedAfter}`)
  }

  if (publishedBefore) {
    filters.push(`published_at:lte:${publishedBefore}`)
  }

  // Add filters to query params
  if (filters.length > 0) {
    queryParams.filters = filters
  }

  // Add sorting
  queryParams.sorts = `${sortBy}:${sortOrder}`

  return withMock(
    {
      items: mockContentItems.slice(0, limit),
      nextCursor: mockContentItems.length > limit ? "mock_cursor_next" : null,
      previousCursor: null,
      total: includeTotal ? mockContentItems.length : null,
    },
    async () => {
      const response = await api.get("/content", { params: queryParams })
      const paginatedSchema = paginatedResponseSchema(contentItemSchema)
      const parsed = paginatedSchema.parse(response.data)

      return {
        items: parsed.items,
        nextCursor: parsed.next_page || null,
        previousCursor: parsed.previous_page || null,
        total: parsed.total !== undefined ? parsed.total : null,
      }
    },
  )
}
