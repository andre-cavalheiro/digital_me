"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useSearchParams } from "next/navigation"
import { Loader2 } from "lucide-react"
import { fetchContentList, type ContentItem, type TwitterPlatformMetadata } from "@/lib/api"
import { TweetCard, SourceCard } from "@/components/content/content-cards"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ContentListSkeleton } from "./content-list-skeleton"
import { ContentFilters } from "./content-filters"

type FetchState = "idle" | "loading" | "error"

export function ContentPage() {
  const searchParams = useSearchParams()
  const [items, setItems] = useState<ContentItem[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState<number | null>(null)
  const [status, setStatus] = useState<FetchState>("idle")
  const [loadingMore, setLoadingMore] = useState(false)
  const sentinelRef = useRef<HTMLDivElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

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
  }, [status, nextCursor, loadMore, loadingMore])

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

  const isLoading = status === "loading" && items.length === 0
  const hasContent = items.length > 0

  return (
    <div className="flex h-full flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Content</h1>
          <p className="text-sm text-muted-foreground">
            {status === "loading" && !hasContent && "Loading..."}
            {status === "idle" && totalCount !== null && `${totalCount.toLocaleString()} pieces of content saved`}
            {status === "idle" && totalCount === null && hasContent && `${items.length} items`}
          </p>
        </div>
        <ContentFilters onFilterChange={handleFilterChange} />
      </div>

      {/* Loading state */}
      {isLoading && <ContentListSkeleton />}

      {/* Error state */}
      {status === "error" && !isLoading && (
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
      {!isLoading && status !== "error" && (
        <>
          {hasContent ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {items.map((item) => {
                // Check if this is a tweet with platform metadata
                const isTwitterContent =
                  item.platform_metadata && "author" in item.platform_metadata && "text" in item.platform_metadata

                if (isTwitterContent) {
                  return <TweetCard key={item.id} item={item} metadata={item.platform_metadata as TwitterPlatformMetadata} />
                }

                return <SourceCard key={item.id} item={item} />
              })}
            </div>
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
          {hasContent && (
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
