import type { User, Organization, Plugin } from "./types"
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

/**
 * Utility to conditionally use mock data or real API call
 * Based on NEXT_PUBLIC_USE_MOCKS environment variable
 */
export function withMock<T>(mockData: T, apiFn: () => Promise<T>): Promise<T> {
  return env.NEXT_PUBLIC_USE_MOCKS ? Promise.resolve(mockData) : apiFn()
}
