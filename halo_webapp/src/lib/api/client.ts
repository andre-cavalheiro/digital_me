import axios from "axios"
import { env } from "@/app/env"
import { auth } from "@/lib/auth/firebase"
import { handleApiError } from "./errors"

/**
 * Axios instance configured for the Fury API
 * - Includes Firebase authentication token in requests
 * - Has 45 second timeout
 * - Handles errors with typed error handling
 */
export const api = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: 45000, // 45 seconds timeout
})

// Request interceptor: Include Firebase token in each request
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: Handle errors with typed error handling
api.interceptors.response.use((response) => response, handleApiError)
