import { z } from "zod"
import { api } from "./client"
import { withMock } from "./mocks"
import { authorSchema, type Author } from "./schemas/author"
import { paginatedResponseSchema } from "./schemas/pagination"

// Mock data for development
const mockAuthors: Author[] = [
  {
    id: 1,
    platform: "x",
    external_id: "123456789",
    display_name: "Tech Insights",
    handle: "@techinsights",
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=techinsights",
    profile_url: "https://x.com/techinsights",
    bio: "Exploring the intersection of technology and society. Thoughts on AI, startups, and innovation.",
    follower_count: 125000,
    following_count: 450,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    platform: "x",
    external_id: "987654321",
    display_name: "Sarah Chen",
    handle: "@sarahchen",
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=sarahchen",
    profile_url: "https://x.com/sarahchen",
    bio: "Product designer & tech writer. Building better digital experiences.",
    follower_count: 45000,
    following_count: 320,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    platform: "x",
    external_id: "456789123",
    display_name: "AI Research Daily",
    handle: "@airesearch",
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=airesearch",
    profile_url: "https://x.com/airesearch",
    bio: "Daily updates on AI research papers, breakthroughs, and industry trends.",
    follower_count: 89000,
    following_count: 150,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

export interface FetchAuthorsParams {
  limit?: number
  offset?: number
  platform?: string
  sortBy?: "created_at" | "display_name" | "follower_count"
  sortOrder?: "asc" | "desc"
}

export async function fetchAuthors(params: FetchAuthorsParams = {}): Promise<Author[]> {
  const { limit = 20, offset = 0, platform, sortBy = "display_name", sortOrder = "asc" } = params

  const queryParams: Record<string, string> = {
    size: String(limit),
  }

  if (offset > 0) {
    queryParams.offset = String(offset)
  }

  if (platform) {
    queryParams.filters = `platform[eq]:${platform}`
  }

  queryParams.sorts = `${sortBy}:${sortOrder}`

  return withMock(mockAuthors, async () => {
    const response = await api.get("/authors", { params: queryParams })
    const paginatedSchema = paginatedResponseSchema(authorSchema)
    const parsed = paginatedSchema.parse(response.data)
    return parsed.items
  })
}

export async function fetchAuthor(id: number): Promise<Author> {
  return withMock(
    mockAuthors.find((author) => author.id === id) ?? mockAuthors[0],
    async () => {
      const response = await api.get(`/authors/${id}`)
      return authorSchema.parse(response.data)
    },
  )
}

export interface AuthorWithContentCount extends Author {
  content_count?: number
}

export interface FetchAuthorsWithCountParams {
  size?: number
  cursor?: string | null
  platform?: string
  sortBy?: "id" | "platform" | "display_name" | "created_at"
  sortOrder?: "asc" | "desc"
  includeTotal?: boolean
}

export interface AuthorsListResponse {
  items: AuthorWithContentCount[]
  nextCursor: string | null
  total?: number | null
}

export async function fetchAuthorsWithContentCount(
  params: FetchAuthorsWithCountParams = {},
): Promise<AuthorsListResponse> {
  const { size = 20, cursor, platform, sortBy = "display_name", sortOrder = "asc", includeTotal = false } = params

  return withMock(
    {
      items: mockAuthors.slice(0, size).map((author) => ({
        ...author,
        content_count: Math.floor(Math.random() * 100) + 1,
      })),
      nextCursor: mockAuthors.length > size ? "mock_cursor" : null,
      total: includeTotal ? mockAuthors.length : null,
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

      if (platform) {
        queryParams.filters = `platform[eq]:${platform}`
      }

      queryParams.sorts = `${sortBy}:${sortOrder}`

      const response = await api.get("/authors", {
        params: queryParams,
      })
      const paginatedSchema = paginatedResponseSchema(authorSchema)
      const parsed = paginatedSchema.parse(response.data)

      return {
        items: parsed.items,
        nextCursor: parsed.next_page || null,
        total: parsed.total !== undefined ? parsed.total : null,
      }
    },
  )
}
