import { api } from "./client"
import { pluginSchema, paginatedResponseSchema } from "./schemas/plugin"
import { withMock, mockPlugins } from "./mocks"
import type { Plugin, PluginCreate, PaginatedResponse } from "./types"

/**
 * Fetches all plugins for the current organization
 */
export async function fetchPlugins(): Promise<Plugin[]> {
  return withMock(mockPlugins, async () => {
    try {
      const response = await api.get<PaginatedResponse<Plugin>>("/plugins")

      // Handle both paginated and direct array responses
      const data = response.data.items || response.data

      // Validate the response
      const paginatedSchema = paginatedResponseSchema(pluginSchema)
      const validated = paginatedSchema.safeParse(response.data)

      if (validated.success) {
        return validated.data.items
      }

      // Fallback for direct array response
      return Array.isArray(data) ? data : []
    } catch (error) {
      console.error("Error fetching plugins:", error)
      // Return empty array on error to prevent crashes
      return []
    }
  })
}

/**
 * Creates a new plugin
 */
export async function createPlugin(plugin: PluginCreate): Promise<Plugin> {
  return withMock(
    {
      id: Math.floor(Math.random() * 1000),
      organization_id: 1,
      dataSource: plugin.data_source,
      title: plugin.title,
      credentials: plugin.credentials || {},
      properties: plugin.properties || {},
      created_at: new Date().toISOString(),
    },
    async () => {
      const response = await api.post<Plugin>("/plugins", plugin)
      return pluginSchema.parse(response.data)
    },
  )
}

/**
 * Deletes a plugin by ID
 */
export async function deletePlugin(id: number): Promise<void> {
  if (process.env.NEXT_PUBLIC_USE_MOCKS === "true") {
    console.log("Mock: deleting plugin", { id })
    return
  }

  await api.delete(`/plugins/${id}`)
}

/**
 * Trigger a background job for a plugin
 */
export async function triggerPluginJob(id: number, jobType: string, jobParams: Record<string, any> = {}): Promise<any> {
  if (process.env.NEXT_PUBLIC_USE_MOCKS === "true") {
    console.log("Mock: triggering plugin job", { id, jobType, jobParams })
    return { task_id: "mock-task-id" }
  }

  const response = await api.post(`/plugins/${id}/trigger-job`, {
    job_type: jobType,
    job_params: jobParams,
  })
  return response.data
}
