"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useSearchParams } from "next/navigation"
import { Loader2 } from "lucide-react"
import { fetchContentList, searchContent, type ContentItem } from "@/lib/api"
import { ContentRenderer } from "@/components/content/content-renderer"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ContentListSkeleton } from "./content-list-skeleton"
import { ContentFilters } from "./content-filters"
import { ContentSearchInput } from "./content-search-input"

type FetchState = "idle" | "loading" | "error"
type ContentMode = "browsing" | "searching"

export function ContentPage() {
  const searchParams = useSearchParams()
  const [items, setItems] = useState<ContentItem[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState<number | null>(null)
  const [status, setStatus] = useState<FetchState>("idle")
  const [loadingMore, setLoadingMore] = useState(false)
  const sentinelRef = useRef<HTMLDivElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  // Search state
  const [mode, setMode] = useState<ContentMode>("browsing")
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<ContentItem[]>([])
  const [searchStatus, setSearchStatus] = useState<FetchState>("idle")
  const searchRequestRef = useRef(0)
  const isManualSearchRef = useRef(false)

  // Get sort parameters from URL
  const sortParam = searchParams.get("sort") || "newest"
  const sortOrder = sortParam === "oldest" ? "asc" : "desc"

  // Initial load
  useEffect(() => {
    let mounted = true

    const loadInitial = async () => {
      setStatus("loading")
      try {
        const response = await fetchContentList({
          limit: 20,
          includeTotal: true,
          sortBy: "published_at",
          sortOrder: sortOrder,
        })

        if (mounted) {
          setItems(response.items)
          setNextCursor(response.nextCursor)
          setTotalCount(response.total)
          setStatus("idle")
        }
      } catch (error) {
        console.error("Failed to load content", error)
        if (mounted) {
          setStatus("error")
        }
      }
    }

    loadInitial()

    return () => {
      mounted = false
    }
  }, [sortOrder])

  // Load more function
  const loadMore = useCallback(async () => {
    if (!nextCursor || loadingMore) return

    setLoadingMore(true)
    try {
      const response = await fetchContentList({
        cursor: nextCursor,
        limit: 20,
        sortBy: "published_at",
        sortOrder: sortOrder,
      })

      setItems((prev) => [...prev, ...response.items])
      setNextCursor(response.nextCursor)
    } catch (error) {
      console.error("Failed to load more content", error)
    } finally {
      setLoadingMore(false)
    }
  }, [nextCursor, loadingMore, sortOrder])

  // Setup IntersectionObserver for infinite scroll
  useEffect(() => {
    if (!sentinelRef.current || status !== "idle") return

    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      if (mode === "searching") return
      if (entry.isIntersecting && nextCursor && !loadingMore) {
        loadMore()
      }
    }

    observerRef.current = new IntersectionObserver(handleIntersection, {
      threshold: 0.1,
      rootMargin: "100px",
    })

    observerRef.current.observe(sentinelRef.current)

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [status, nextCursor, loadMore, loadingMore, mode])

  // Search logic with race condition protection
  const runSearch = useCallback(async (query: string) => {
    if (!query) return
    const requestId = ++searchRequestRef.current
    setSearchStatus("loading")

    try {
      const results = await searchContent({ query, limit: 50 })
      if (searchRequestRef.current !== requestId) return
      setSearchResults(results)
      setSearchStatus("idle")
    } catch (error) {
      console.error("Failed to search content", error)
      if (searchRequestRef.current !== requestId) return
      setSearchStatus("error")
    }
  }, [])

  // Manual search trigger (for Enter key)
  const handleSearch = useCallback(() => {
    if (searchQuery.trim().length === 0) {
      // Empty query - return to browsing
      setMode("browsing")
      setSearchResults([])
      setSearchStatus("idle")
      isManualSearchRef.current = false
      return
    }
    // Trigger search immediately regardless of length
    isManualSearchRef.current = true
    setMode("searching")
    void runSearch(searchQuery)
  }, [searchQuery, runSearch])

  // Debounced search with mode switching
  useEffect(() => {
    const MIN_QUERY_LENGTH = 8

    if (searchQuery.length < MIN_QUERY_LENGTH) {
      // Don't clear if this is a manual search in progress
      if (mode === "searching" && !isManualSearchRef.current) {
        setMode("browsing")
        setSearchResults([])
        setSearchStatus("idle")
      }
      return
    }

    // Reset manual search flag for auto-searches
    isManualSearchRef.current = false
    setMode("searching")
    setSearchStatus("loading")
    const handle = setTimeout(() => {
      void runSearch(searchQuery)
    }, 450)

    return () => clearTimeout(handle)
  }, [searchQuery, runSearch, mode])

  const handleRetry = async () => {
    setStatus("loading")
    try {
      const response = await fetchContentList({
        limit: 20,
        includeTotal: true,
        sortBy: "published_at",
        sortOrder: sortOrder,
      })

      setItems(response.items)
      setNextCursor(response.nextCursor)
      setTotalCount(response.total)
      setStatus("idle")
    } catch (error) {
      console.error("Failed to retry loading content", error)
      setStatus("error")
    }
  }

  const handleFilterChange = () => {
    // Filters are managed via URL params, so this is just a placeholder
    // The useEffect will automatically re-fetch when sortOrder changes
  }

  // Display logic based on mode
  const displayItems = mode === "searching" ? searchResults : items
  const displayStatus = mode === "searching" ? searchStatus : status
  const isLoading = displayStatus === "loading" && displayItems.length === 0
  const hasContent = displayItems.length > 0
  const showInfiniteScroll = mode === "browsing" && hasContent && nextCursor

  return (
    <div className="flex h-full flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Content</h1>
          <p className="text-sm text-muted-foreground">
            {displayStatus === "loading" && !hasContent && "Loading..."}
            {mode === "searching" && searchStatus === "idle" && `${searchResults.length} result${searchResults.length !== 1 ? 's' : ''}`}
            {mode === "browsing" && status === "idle" && totalCount !== null && `${totalCount.toLocaleString()} pieces of content saved`}
            {mode === "browsing" && status === "idle" && totalCount === null && hasContent && `${items.length} items`}
          </p>
        </div>
        <ContentFilters onFilterChange={handleFilterChange} />
      </div>

      {/* Search Input */}
      <ContentSearchInput
        value={searchQuery}
        onChange={setSearchQuery}
        onClear={() => setSearchQuery("")}
        onSearch={handleSearch}
        isSearching={mode === "searching" && searchStatus === "loading"}
      />

      {/* Loading state */}
      {isLoading && <ContentListSkeleton />}

      {/* Error state */}
      {displayStatus === "error" && !isLoading && (
        <Card className="border-destructive/20 bg-destructive/5 text-destructive">
          <CardHeader>
            <CardTitle>Unable to load content</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm">Check your connection or try again.</p>
            <Button variant="outline" onClick={handleRetry}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Content grid */}
      {!isLoading && displayStatus !== "error" && (
        <>
          {hasContent ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {displayItems.map((item) => (
                <ContentRenderer key={item.id} item={item} />
              ))}
            </div>
          ) : mode === "searching" ? (
            <Card className="border-dashed text-muted-foreground">
              <CardHeader>
                <CardTitle>No results found</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">Try a different search query.</p>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed text-muted-foreground">
              <CardHeader>
                <CardTitle>No content yet</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">Connect a source to get started.</p>
              </CardContent>
            </Card>
          )}

          {/* Infinite scroll sentinel */}
          {showInfiniteScroll && (
            <div ref={sentinelRef} className="flex justify-center py-4">
              {loadingMore && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading more...
                </div>
              )}
              {!loadingMore && nextCursor && (
                <Button variant="outline" onClick={loadMore}>
                  Load More
                </Button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
