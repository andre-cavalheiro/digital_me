import { api } from "./client"
import { organizationSchema } from "./schemas/organization"
import { withMock, mockOrganization } from "./mocks"
import type { Organization } from "./types"

/**
 * Fetches the current user's organization
 */
export async function fetchOrganization(): Promise<Organization> {
  return withMock(mockOrganization, async () => {
    const response = await api.get<Organization>("/organizations/self")
    return organizationSchema.parse(response.data)
  })
}

/**
 * Creates a new organization
 */
export async function createOrganization(name: string): Promise<Organization> {
  return withMock(mockOrganization, async () => {
    const response = await api.post<Organization>("/organizations", { name })
    return organizationSchema.parse(response.data)
  })
}
