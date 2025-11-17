/**
 * API Client - Central export point
 *
 * This module provides organized access to all API functionality.
 * Import from domain-specific modules for better tree-shaking.
 */

// Domain-specific API modules
export * from "./users"
export * from "./organizations"
export * from "./plugins"

// Core exports
export { api } from "./client"
export { ApiError, handleApiError } from "./errors"
export { withMock } from "./mocks"

// Types
export type * from "./types"
