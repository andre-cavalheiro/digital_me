import type { User, Organization, Plugin, Document, DocumentSection, Citation, Conversation, Message } from "./types"
import type { ContentItem } from "./schemas/content"
import { env } from "@/app/env"

export const mockOrganization: Organization = {
  id: 1,
  name: "Mocked Organization",
}

export const mockUser: User = {
  id: 1,
  name: "Mocked User",
  email: "test@example.com",
  organization_id: 1,
}

export const mockPlugins: Plugin[] = []

export const mockDocuments: Document[] = [
  { id: 1, title: "AI Collaboration Trends", created_at: "2024-01-10T12:00:00Z", updated_at: "2024-01-10T12:00:00Z" },
  { id: 2, title: "Creative Workflows", created_at: "2024-01-08T09:15:00Z", updated_at: "2024-01-09T18:30:00Z" },
  { id: 3, title: "Citations and Context", created_at: "2024-01-05T16:45:00Z", updated_at: "2024-01-07T10:20:00Z" },
]

export const mockDocumentContents: Record<number, DocumentSection[]> = {
  1: [
    {
      id: 1,
      document_id: 1,
      content: "Artificial intelligence has fundamentally transformed how we approach creative work.",
      order_index: 0,
      word_count: 11,
      updated_at: "2024-01-10T12:00:00Z",
    },
    {
      id: 2,
      document_id: 1,
      content: "The key to effective AI collaboration lies in understanding both its strengths and limitations.",
      order_index: 1,
      word_count: 14,
      updated_at: "2024-01-10T12:00:00Z",
    },
  ],
  2: [
    {
      id: 3,
      document_id: 2,
      content: "Looking ahead, the integration of AI into creative workflows will likely become as ubiquitous as spell-checkers.",
      order_index: 0,
      word_count: 17,
      updated_at: "2024-01-09T18:30:00Z",
    },
    {
      id: 4,
      document_id: 2,
      content: "Creators who adapt will thrive.",
      order_index: 1,
      word_count: 5,
      updated_at: "2024-01-09T18:30:00Z",
    },
  ],
}

export const mockContentItems: ContentItem[] = [
  {
    id: 11,
    title: "The Future of Creative Work",
    excerpt: "AI tools as collaborative partners that augment capabilities.",
    summary: "AI tools as collaborative partners that augment capabilities.",
    author: "Ethan Foster",
    author_id: null,
    published_at: "2024-01-03T09:00:00Z",
    source_url: "https://example.com/future-of-work",
    platform_metadata: undefined,
    body: undefined,
  },
  {
    id: 12,
    title: "Curation Over Creation",
    excerpt: "Abundance shifts the bottleneck from generating ideas to selecting the right ones.",
    summary: "Abundance shifts the bottleneck from generating ideas to selecting the right ones.",
    author: "Fiona Green",
    author_id: null,
    published_at: "2024-01-02T10:00:00Z",
    source_url: "https://example.com/curation",
    platform_metadata: undefined,
    body: undefined,
  },
  {
    id: 13,
    title: "Adapting to AI Integration",
    excerpt: "Creators who embrace new tools gain significant advantages over those who resist change.",
    summary: "Creators who embrace new tools gain significant advantages over those who resist change.",
    author: "George Harris",
    author_id: null,
    published_at: "2024-01-01T08:00:00Z",
    source_url: "https://example.com/adapting-ai",
    platform_metadata: undefined,
    body: undefined,
  },
]

export const mockCitations: Citation[] = [
  { id: 101, document_id: 1, content_id: 11, marker: 1, position: 42 },
  { id: 102, document_id: 1, content_id: 12, marker: 2, position: 128 },
]

export const mockConversations: Conversation[] = [
  { id: 201, title: "Kickoff Ideas", document_id: 1, created_at: "2024-01-10T12:00:00Z" },
  { id: 202, title: "AI Adoption Risks", document_id: null, created_at: "2024-01-08T09:00:00Z" },
]

export const mockMessages: Message[] = [
  {
    id: 301,
    conversation_id: 201,
    role: "user",
    content: "How should I frame AI benefits?",
    created_at: "2024-01-10T12:01:00Z",
    status: "completed",
    metadata: { mock: true },
  },
  {
    id: 302,
    conversation_id: 201,
    role: "assistant",
    content: "Lean on augmentation, not replacement.",
    created_at: "2024-01-10T12:01:30Z",
    status: "completed",
    metadata: { mock: true },
  },
]

/**
 * Utility to conditionally use mock data or real API call
 * Based on NEXT_PUBLIC_USE_MOCKS environment variable
 */
export function withMock<T>(mockData: T, apiFn: () => Promise<T>): Promise<T> {
  return env.NEXT_PUBLIC_USE_MOCKS ? Promise.resolve(mockData) : apiFn()
}
