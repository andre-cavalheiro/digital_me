import { api } from "./client"
import { withMock, mockContentItems } from "./mocks"
import { contentItemSchema } from "./schemas/content"
import { paginatedResponseSchema } from "./schemas/pagination"
import type { ContentItem } from "./types"

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
