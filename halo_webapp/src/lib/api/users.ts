import { api } from "./client"
import { userSchema } from "./schemas/user"
import { withMock, mockUser } from "./mocks"
import type { User } from "./types"

/**
 * Fetches the current authenticated user
 */
export async function fetchCurrentUser(): Promise<User> {
  return withMock(mockUser, async () => {
    const response = await api.get<User>("/users/self")
    return userSchema.parse(response.data)
  })
}
