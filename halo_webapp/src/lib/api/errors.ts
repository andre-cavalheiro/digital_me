import type { AxiosError } from "axios"

/**
 * Custom API error class with additional context
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: unknown,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

/**
 * Handles axios errors and converts them to typed ApiError
 * Used in the axios response interceptor
 */
export function handleApiError(error: AxiosError): never {
  if (error.response) {
    // Server responded with error status
    throw new ApiError(
      error.response.statusText || "API Error",
      error.response.status,
      error.response.data,
    )
  } else if (error.request) {
    // Request made but no response received
    throw new ApiError("No response from server")
  } else {
    // Something else happened
    throw new ApiError(error.message)
  }
}
