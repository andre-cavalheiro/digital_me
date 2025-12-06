import { z } from "zod"
import { api } from "./client"
import { withMock, mockContentItems } from "./mocks"
import { collectionSchema, type Collection } from "./schemas/collection"
import { paginatedResponseSchema } from "./schemas/pagination"
import { fetchContentList } from "./content"
import type { ContentItem, ContentListResponse } from "./types"

// Author statistics types
export interface AuthorContribution {
  authorId: number
  displayName: string
  handle: string
  avatarUrl: string | null
  contentCount: number
  percentage: number
}

export interface CollectionAuthorStatistics {
  collectionId: number
  totalContentCount: number
  uniqueAuthorCount: number
  contributors: AuthorContribution[]
}

// Mock data for development
const mockCollections: Collection[] = [
  {
    id: 1,
    organization_id: 1,
    type: "bookmark_folder",
    platform: "x",
    name: "AI & Machine Learning",
    external_id: "folder_123",
    description: "Articles and threads about AI developments, ML research, and practical applications",
    collection_url: null,
    last_synced_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    organization_id: 1,
    type: "bookmark_folder",
    platform: "x",
    name: "Product Design",
    external_id: "folder_456",
    description: "Best practices, case studies, and insights on product and UX design",
    collection_url: null,
    last_synced_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    organization_id: 1,
    type: "bookmark_folder",
    platform: "x",
    name: "Startup Lessons",
    external_id: "folder_789",
    description: "Founder stories, startup advice, and entrepreneurship wisdom",
    collection_url: null,
    last_synced_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 4,
    organization_id: 1,
    type: "bookmark_folder",
    platform: "x",
    name: "Technical Writing",
    external_id: "folder_101",
    description: "Resources on writing technical documentation, blog posts, and tutorials",
    collection_url: null,
    last_synced_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

export interface FetchCollectionsParams {
  limit?: number
  offset?: number
  platform?: string
  type?: string
  sortBy?: "created_at" | "name" | "last_synced_at"
  sortOrder?: "asc" | "desc"
}

export async function fetchCollections(params: FetchCollectionsParams = {}): Promise<Collection[]> {
  const { limit = 20, offset = 0, platform, type, sortBy = "name", sortOrder = "asc" } = params

  const queryParams: Record<string, string | string[]> = {
    size: String(limit),
  }

  if (offset > 0) {
    queryParams.offset = String(offset)
  }

  const filters: string[] = []
  if (platform) {
    filters.push(`platform:eq:${platform}`)
  }
  if (type) {
    filters.push(`type:eq:${type}`)
  }

  if (filters.length > 0) {
    queryParams.filters = filters
  }

  queryParams.sorts = `${sortBy}:${sortOrder}`

  return withMock(mockCollections, async () => {
    const response = await api.get("/collections", { params: queryParams })
    const paginatedSchema = paginatedResponseSchema(collectionSchema)
    const parsed = paginatedSchema.parse(response.data)
    return parsed.items
  })
}

export async function fetchCollection(id: number): Promise<Collection> {
  return withMock(
    mockCollections.find((collection) => collection.id === id) ?? mockCollections[0],
    async () => {
      const response = await api.get(`/collections/${id}`)
      return collectionSchema.parse(response.data)
    },
  )
}

export interface CollectionWithContentCount extends Collection {
  content_count?: number
}

export interface FetchCollectionsWithCountParams {
  size?: number
  cursor?: string | null
  platformType?: string
  search?: string
  sortBy?: "id" | "platform_type" | "name" | "created_at"
  sortOrder?: "asc" | "desc"
  includeTotal?: boolean
}

export interface CollectionsListResponse {
  items: CollectionWithContentCount[]
  nextCursor: string | null
  total?: number | null
}

export async function fetchCollectionsWithContentCount(
  params: FetchCollectionsWithCountParams = {},
): Promise<CollectionsListResponse> {
  const { size = 20, cursor, platformType, search, sortBy = "name", sortOrder = "asc", includeTotal = false } = params

  return withMock(
    {
      items: mockCollections.slice(0, size).map((collection) => ({
        ...collection,
        content_count: Math.floor(Math.random() * 50) + 1,
      })),
      nextCursor: mockCollections.length > size ? "mock_cursor" : null,
      total: includeTotal ? mockCollections.length : null,
    },
    async () => {
      const queryParams: Record<string, any> = {
        size: String(size),
      }

      if (cursor) {
        queryParams.cursor = cursor
      }

      if (includeTotal) {
        queryParams.includeTotal = "true"
      }

      // Build filters array
      const filters: string[] = []
      if (platformType) {
        filters.push(`platform_type:eq:${platformType}`)
      }
      if (search) {
        filters.push(`name:ilike:%${search}%`)
      }
      if (filters.length > 0) {
        queryParams.filters = filters
      }

      queryParams.sorts = `${sortBy}:${sortOrder}`

      const response = await api.get("/collections", {
        params: queryParams,
      })
      const paginatedSchema = paginatedResponseSchema(collectionSchema)
      const parsed = paginatedSchema.parse(response.data)

      return {
        items: parsed.items,
        nextCursor: parsed.next_page || null,
        total: parsed.total !== undefined ? parsed.total : null,
      }
    },
  )
}

/**
 * Fetch collections by their IDs
 * Used to ensure previously selected collections are loaded even if not in first page
 */
export async function fetchCollectionsByIds(ids: number[]): Promise<CollectionWithContentCount[]> {
  if (ids.length === 0) return []

  return withMock(
    mockCollections.filter((c) => ids.includes(c.id)).map((collection) => ({
      ...collection,
      content_count: Math.floor(Math.random() * 50) + 1,
    })),
    async () => {
      const queryParams: Record<string, any> = {
        size: String(ids.length),
        filters: `id:in:${ids.join(",")}`,
      }

      const response = await api.get("/collections", {
        params: queryParams,
      })
      const paginatedSchema = paginatedResponseSchema(collectionSchema)
      const parsed = paginatedSchema.parse(response.data)

      return parsed.items
    },
  )
}

export interface FetchCollectionContentParams {
  cursor?: string | null
  limit?: number
  sortBy?: "published_at" | "created_at"
  sortOrder?: "asc" | "desc"
  includeTotal?: boolean
}

/**
 * Fetch content items in a specific collection
 * Uses the unified GET /content endpoint with collection_id filter
 */
export async function fetchCollectionContent(
  collectionId: number,
  params: FetchCollectionContentParams = {},
): Promise<ContentListResponse> {
  const { cursor, limit = 20, sortBy = "published_at", sortOrder = "desc", includeTotal = false } = params

  // Use the unified content endpoint with collection filter
  return fetchContentList({
    cursor,
    limit,
    collectionIds: [collectionId],
    sortBy,
    sortOrder,
    includeTotal,
  })
}

/**
 * Fetch author contribution statistics for a collection
 */
export async function fetchCollectionAuthorStatistics(
  collectionId: number,
): Promise<CollectionAuthorStatistics> {
  // Mock data for development
  const mockStats: CollectionAuthorStatistics = {
    collectionId,
    totalContentCount: 150,
    uniqueAuthorCount: 5,
    contributors: [
      {
        authorId: 1,
        displayName: "Tech Insights",
        handle: "@techinsights",
        avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=techinsights",
        contentCount: 75,
        percentage: 50.0,
      },
      {
        authorId: 2,
        displayName: "Sarah Chen",
        handle: "@sarahchen",
        avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=sarahchen",
        contentCount: 45,
        percentage: 30.0,
      },
      {
        authorId: 3,
        displayName: "AI Research Daily",
        handle: "@airesearch",
        avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=airesearch",
        contentCount: 20,
        percentage: 13.3,
      },
      {
        authorId: 4,
        displayName: "John Doe",
        handle: "@johndoe",
        avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=johndoe",
        contentCount: 7,
        percentage: 4.7,
      },
      {
        authorId: 5,
        displayName: "Jane Smith",
        handle: "@janesmith",
        avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=janesmith",
        contentCount: 3,
        percentage: 2.0,
      },
    ],
  }

  return withMock(mockStats, async () => {
    const response = await api.get(`/collections/${collectionId}/author-statistics`)
    const payload = response.data as any

    return {
      collectionId: Number(payload.collectionId ?? payload.collection_id ?? collectionId),
      totalContentCount: Number(payload.totalContentCount ?? payload.total_content_count ?? 0),
      uniqueAuthorCount: Number(
        payload.uniqueAuthorCount ?? payload.unique_author_count ?? payload.contributors?.length ?? 0,
      ),
      contributors: (payload.contributors ?? []).map((contributor: any) => {
        const authorId = contributor.authorId ?? contributor.author_id
        return {
          authorId:
            authorId !== undefined && authorId !== null ? Number(authorId) : Number.NaN,
          displayName:
            contributor.displayName ??
            contributor.display_name ??
            contributor.handle ??
            "Unknown author",
          handle: contributor.handle ?? "",
          avatarUrl: contributor.avatarUrl ?? contributor.avatar_url ?? null,
          contentCount: Number(contributor.contentCount ?? contributor.content_count ?? 0),
          percentage: Number(contributor.percentage ?? 0),
        }
      }),
    }
  })
}
