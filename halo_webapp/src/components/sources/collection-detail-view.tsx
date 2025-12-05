"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, ExternalLink, FolderOpen, Loader2 } from "lucide-react"
import { fetchCollectionContent, type CollectionWithContentCount } from "@/lib/api/collections"
import type { ContentItem, TwitterPlatformMetadata } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TweetCard, SourceCard } from "@/components/content/content-cards"
import { CollectionAuthorPieChart } from "./collection-author-pie-chart"

type CollectionDetailViewProps = {
  collection: CollectionWithContentCount
}

const PAGE_SIZE = 20

export function CollectionDetailView({ collection }: CollectionDetailViewProps) {
  const router = useRouter()

  const [content, setContent] = useState<ContentItem[]>([])
  const [contentStatus, setContentStatus] = useState<"idle" | "loading" | "error">("loading")
  const [contentCursor, setContentCursor] = useState<string | null>(null)
  const [contentHasMore, setContentHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [contentTotal, setContentTotal] = useState<number | null>(null)

  const sentinelRef = useRef<HTMLDivElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  // Load initial content
  useEffect(() => {
    let mounted = true

    const loadContent = async () => {
      setContentStatus("loading")
      try {
        const response = await fetchCollectionContent(collection.id, {
          limit: PAGE_SIZE,
          includeTotal: true,
        })
        if (mounted) {
          setContent(response.items)
          setContentCursor(response.nextCursor)
          setContentHasMore(!!response.nextCursor)
          setContentTotal(response.total ?? null)
          setContentStatus("idle")
        }
      } catch (error) {
        console.error("Failed to load collection content", error)
        if (mounted) {
          setContentStatus("error")
        }
      }
    }

    loadContent()

    return () => {
      mounted = false
    }
  }, [collection.id])

  // Load more content
  const loadMoreContent = useCallback(async () => {
    if (!contentHasMore || loadingMore || !contentCursor) return

    setLoadingMore(true)
    try {
      const response = await fetchCollectionContent(collection.id, {
        limit: PAGE_SIZE,
        cursor: contentCursor,
      })
      setContent((prev) => [...prev, ...response.items])
      setContentCursor(response.nextCursor)
      setContentHasMore(!!response.nextCursor)
    } catch (error) {
      console.error("Failed to load more content", error)
    } finally {
      setLoadingMore(false)
    }
  }, [collection.id, contentCursor, contentHasMore, loadingMore])

  // Setup IntersectionObserver for infinite scroll
  useEffect(() => {
    if (!sentinelRef.current || contentStatus !== "idle") return

    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      if (entry.isIntersecting && contentHasMore && !loadingMore) {
        loadMoreContent()
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
  }, [contentStatus, contentHasMore, loadMoreContent, loadingMore])

  const handleExternalUrl = () => {
    if (collection.collection_url) {
      window.open(collection.collection_url, "_blank", "noopener,noreferrer")
    }
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }

  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now.getTime() - date.getTime()
    const diffInMinutes = Math.floor(diffInMs / 60000)
    const diffInHours = Math.floor(diffInMinutes / 60)
    const diffInDays = Math.floor(diffInHours / 24)

    if (diffInMinutes < 1) return "just now"
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInHours < 24) return `${diffInHours}h ago`
    if (diffInDays < 7) return `${diffInDays}d ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`

    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
  }

  const isContentLoading = contentStatus === "loading" && content.length === 0

  return (
    <div className="flex h-full flex-col gap-6">
      {/* Back button */}
      <div>
        <Button
          variant="ghost"
          onClick={() => router.push("/sources")}
          className="w-fit"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Sources
        </Button>
      </div>

      {/* Collection header card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <div className="flex h-20 w-20 flex-shrink-0 items-center justify-center rounded-xl bg-sky-100">
              <FolderOpen className="h-10 w-10 text-sky-600" />
            </div>

            {/* Collection info */}
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h1 className="text-2xl font-bold text-slate-900">{collection.name}</h1>
                  <p className="text-sm capitalize text-slate-500">{collection.type.replace(/_/g, " ")}</p>
                </div>
                {collection.collection_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExternalUrl}
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    View Collection
                  </Button>
                )}
              </div>

              {/* Description */}
              {collection.description && (
                <p className="mt-3 text-sm leading-relaxed text-slate-700">{collection.description}</p>
              )}

              {/* Stats */}
              <div className="mt-4 flex flex-wrap gap-6 text-sm">
                {contentTotal !== null && (
                  <div>
                    <span className="font-semibold text-slate-900">
                      {formatNumber(contentTotal)}
                    </span>
                    <span className="ml-1 text-slate-500">Items Saved</span>
                  </div>
                )}
                {collection.last_synced_at && (
                  <div>
                    <span className="text-slate-500">Last synced: </span>
                    <span className="font-medium text-slate-700">
                      {formatRelativeTime(collection.last_synced_at)}
                    </span>
                  </div>
                )}
                {collection.platform && (
                  <div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">
                      {collection.platform}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contributor ranking */}
      <CollectionAuthorPieChart collectionId={collection.id} />

      {/* Content section */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          Content
          {contentTotal !== null && contentTotal > 0 && (
            <span className="ml-2 text-base font-normal text-slate-500">
              ({contentTotal})
            </span>
          )}
        </h2>

        {isContentLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          </div>
        )}

        {contentStatus === "error" && !isContentLoading && (
          <Card className="border-destructive/20 bg-destructive/5 text-destructive">
            <CardHeader>
              <CardTitle>Unable to load content</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Failed to load content for this collection.</p>
            </CardContent>
          </Card>
        )}

        {!isContentLoading && contentStatus !== "error" && (
          <>
            {content.length > 0 ? (
              <>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {content.map((item) => {
                    // Check if this is a tweet
                    const isTweet =
                      item.platform_metadata &&
                      typeof item.platform_metadata === "object" &&
                      "author" in item.platform_metadata

                    if (isTweet) {
                      return (
                        <TweetCard
                          key={item.id}
                          item={item}
                          metadata={item.platform_metadata as TwitterPlatformMetadata}
                        />
                      )
                    }

                    return <SourceCard key={item.id} item={item} />
                  })}
                </div>

                {/* Infinite scroll sentinel */}
                <div ref={sentinelRef} className="flex justify-center py-4">
                  {loadingMore && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading more...
                    </div>
                  )}
                  {!loadingMore && contentHasMore && (
                    <Button variant="outline" onClick={loadMoreContent}>
                      Load More
                    </Button>
                  )}
                </div>
              </>
            ) : (
              <Card className="border-dashed text-muted-foreground">
                <CardHeader>
                  <CardTitle>No content yet</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">
                    No content has been saved in this collection yet.
                  </p>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  )
}
