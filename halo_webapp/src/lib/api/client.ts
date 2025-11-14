import axios, { type AxiosError } from "axios"
import type {
  Organization,
  User,
  PaginatedResponse,
  Plugin,
  PluginCreate,
  Project,
  ProjectCreate,
  ProjectPublish,
} from "./types"
import { mockOrganization, mockUser } from "./mocks"
import { env } from "@/app/env"
import { auth } from "@/lib/auth/firebase"

const api = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: 45000, // 45 seconds timeout
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
    return mockOrganization
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
    return mockOrganization
  }

  try {
    const response = await api.post<Organization>("/organizations", { name })
    return response.data
  } catch (error) {
    console.error("Error creating organization:", error)
    throw error
  }
}

export async function getPlugins(): Promise<Plugin[]> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return []
  }

  try {
    const response = await api.get<PaginatedResponse<Plugin>>("/plugins")
    return response.data.items || response.data
  } catch (error) {
    console.error("Error getting plugins:", error)
    // Return empty array on error to prevent crashes
    return []
  }
}

export async function createPlugin(plugin: PluginCreate): Promise<Plugin> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    return {
      id: Math.floor(Math.random() * 1000),
      organization_id: 1,
      dataSource: plugin.data_source,
      title: plugin.title,
      credentials: plugin.credentials || {},
      properties: plugin.properties || {},
      created_at: new Date().toISOString(),
    }
  }

  try {
    const response = await api.post<Plugin>("/plugins", plugin)
    return response.data
  } catch (error) {
    console.error("Error creating plugin:", error)
    throw error
  }
}

export async function deletePlugin(id: number): Promise<void> {
  if (env.NEXT_PUBLIC_USE_MOCKS) {
    console.log("Mock: deleting plugin", { id })
    return
  }

  try {
    await api.delete(`/plugins/${id}`)
  } catch (error) {
    console.error("Error deleting plugin:", error)
    throw error
  }
}
