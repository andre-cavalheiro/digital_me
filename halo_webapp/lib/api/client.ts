import axios, { type AxiosError } from "axios"
import type { Organization, User, House, HouseSearch, PaginatedResponse  } from "./types"
import { mockOrganizationFree, mockUser, mockHouses, mockHouseSearches } from "./mocks"
import { env } from "@/app/env"
import { auth } from "@/lib/auth/firebase"

const api = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: 10000, // 10 seconds timeout
})

// Add an interceptor to include the Firebase token in each request
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add an interceptor with generic error handling logic
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error("API Error Response:", error.response.data)
      console.error("API Error Status:", error.response.status)
    } else if (error.request) {
      console.error("API Error Request:", error.request)
    } else {
      console.error("API Error Message:", error.message)
    }
    return Promise.reject(error)
  }
)

// Add a response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error("API Error Response:", error.response.data)
      console.error("API Error Status:", error.response.status)
    } else if (error.request) {
      console.error("API Error Request:", error.request)
    } else {
      console.error("API Error Message:", error.message)
    }
    return Promise.reject(error)
  },
)

export async function getUser(): Promise<User> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return mockUser
  }

  try {
    const response = await api.get<User>("/users/self")
    return response.data
  } catch (error) {
    console.error("Error getting user:", error)
    throw error
  }
}

export async function getOrganization(): Promise<Organization> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return mockOrganizationFree
  }

  try {
    const response = await api.get<Organization>("/organizations/self")
    return response.data
  } catch (error) {
    console.error("Error getting organization:", error)
    throw error
  }
}

export async function createOrganization(name: string): Promise<Organization> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return mockOrganizationFree
  }

  try {
    const response = await api.post<Organization>("/organizations", { name })
    return response.data
  } catch (error) {
    console.error("Error creating organization:", error)
    throw error
  }
}

export async function createHouse(house: Omit<House, "id" | "lastUpdatedAt">): Promise<House | null> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return { ...house, id: Math.floor(Math.random() * 1000), lastUpdatedAt: new Date().toISOString() }
  }

  try {
    const response = await api.post<House>("/houses", house)
    return response.data
  } catch (error) {
    if ((error as AxiosError).response?.status === 409) {
      console.warn("House already exists")
      return null
    }
    throw error
  }
}

export async function getHouses(): Promise<PaginatedResponse<House>> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return {
      items: mockHouses,
      total: mockHouses.length,
      current_page: null,
      current_page_backwards: null,
      previous_page: null,
      next_page: null,
    }
  }

  const response = await api.get<PaginatedResponse<House>>("/houses")
  return response.data
}

export async function createHouseSearch(search: Omit<HouseSearch, "id" | "createdAt">): Promise<HouseSearch> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return {
      ...search,
      id: Math.floor(Math.random() * 1000),
      createdAt: new Date().toISOString(),
    }
  }

  const response = await api.post<HouseSearch>("/house-searches", search)
  return response.data
}

export async function getHouseSearches(): Promise<PaginatedResponse<HouseSearch>> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return {
      items: mockHouseSearches,
      total: mockHouseSearches.length,
      current_page: null,
      current_page_backwards: null,
      previous_page: null,
      next_page: null,
    }
  }

  const response = await api.get<PaginatedResponse<HouseSearch>>("/house-searches")
  return response.data
}
