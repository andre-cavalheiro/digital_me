import { api } from "./client"
import { withMock, mockContentItems } from "./mocks"
import { contentItemSchema } from "./schemas/content"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { ContentItem, ContentSearchParams } from "./types"

export async function fetchContentFeed(params?: { limit?: number; sorts?: string }): Promise<ContentItem[]> {
  return withMock(
    mockContentItems,
    async () => {
      const response = await api.get("/content", { params })
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
      const response = await api.get<ContentItem>(`/content/${id}`)
      return contentItemSchema.parse(response.data)
    },
  )
}

export async function searchContent(params: ContentSearchParams): Promise<ContentItem[]> {
  const payload = {
    query: params.query,
    limit: params.limit ?? 20,
    source_ids: params.source_ids,
    source_group_ids: params.source_group_ids,
  }

  return withMock(
    rankMockContent(payload.query, payload.limit ?? 20),
    async () => {
      const response = await api.post(`/content/search`, payload)
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
