import { api } from "./client"
import { userSchema, type User } from "./schemas/user"
import { withMock, mockUser } from "./mocks"

/**
 * Fetches the current authenticated user
 */
export async function fetchCurrentUser(): Promise<User> {
  return withMock({ ...mockUser, id: mockUser.id || 1 }, async () => {
    const response = await api.get<User>("/users/self")
    return userSchema.parse(response.data)
  })
}
