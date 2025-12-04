/**
 * localStorage utilities for storing document source filters
 */

const FILTER_KEY_PREFIX = "document-sources-filter:"
const MAX_STORED_FILTERS = 10 // Keep only recent filters to avoid quota issues

export interface SourceFilters {
  authorIds: number[]
  collectionIds: number[]
}

interface StoredDocumentFilters extends SourceFilters {
  documentId: number
  updatedAt: string
}

/**
 * Get the localStorage key for a document's filters
 */
function getFilterKey(documentId: number): string {
  return `${FILTER_KEY_PREFIX}${documentId}`
}

/**
 * Save document source filters to localStorage
 */
export function saveDocumentFilters(documentId: number, filters: SourceFilters): void {
  try {
    const data: StoredDocumentFilters = {
      ...filters,
      documentId,
      updatedAt: new Date().toISOString(),
    }
    localStorage.setItem(getFilterKey(documentId), JSON.stringify(data))
  } catch (error) {
    if (error instanceof Error && error.name === "QuotaExceededError") {
      console.warn("localStorage quota exceeded, clearing old filters")
      clearOldDocumentFilters()
      // Retry after clearing
      try {
        const data: StoredDocumentFilters = {
          ...filters,
          documentId,
          updatedAt: new Date().toISOString(),
        }
        localStorage.setItem(getFilterKey(documentId), JSON.stringify(data))
      } catch (retryError) {
        console.error("Failed to save filters after clearing old data", retryError)
      }
    } else {
      console.error("Failed to save document filters", error)
    }
  }
}

/**
 * Load document source filters from localStorage
 */
export function loadDocumentFilters(documentId: number): SourceFilters | null {
  try {
    const stored = localStorage.getItem(getFilterKey(documentId))
    if (!stored) return null

    const parsed = JSON.parse(stored) as StoredDocumentFilters

    // Validate the structure
    if (
      typeof parsed === "object" &&
      Array.isArray(parsed.authorIds) &&
      Array.isArray(parsed.collectionIds)
    ) {
      return {
        authorIds: parsed.authorIds,
        collectionIds: parsed.collectionIds,
      }
    }

    return null
  } catch (error) {
    console.error("Failed to load document filters", error)
    return null
  }
}

/**
 * Clear filters for a specific document
 */
export function clearDocumentFilters(documentId: number): void {
  try {
    localStorage.removeItem(getFilterKey(documentId))
  } catch (error) {
    console.error("Failed to clear document filters", error)
  }
}

/**
 * Get all stored document filter keys
 */
function getAllFilterKeys(): string[] {
  const keys: string[] = []
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(FILTER_KEY_PREFIX)) {
        keys.push(key)
      }
    }
  } catch (error) {
    console.error("Failed to get filter keys", error)
  }
  return keys
}

/**
 * Clear old document filters, keeping only the most recent ones
 */
function clearOldDocumentFilters(): void {
  try {
    const keys = getAllFilterKeys()

    // Parse and sort by updatedAt
    const filters = keys
      .map((key) => {
        try {
          const stored = localStorage.getItem(key)
          if (!stored) return null
          const parsed = JSON.parse(stored) as StoredDocumentFilters
          return { key, updatedAt: new Date(parsed.updatedAt).getTime() }
        } catch {
          return null
        }
      })
      .filter((item): item is { key: string; updatedAt: number } => item !== null)
      .sort((a, b) => b.updatedAt - a.updatedAt)

    // Remove all but the most recent MAX_STORED_FILTERS
    const toRemove = filters.slice(MAX_STORED_FILTERS)
    toRemove.forEach((item) => {
      localStorage.removeItem(item.key)
    })
  } catch (error) {
    console.error("Failed to clear old document filters", error)
  }
}
