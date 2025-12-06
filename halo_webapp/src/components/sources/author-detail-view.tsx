"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { ArrowLeft, ExternalLink, User, Loader2 } from "lucide-react"
import { fetchAuthorContent, type AuthorWithContentCount } from "@/lib/api/authors"
import type { ContentItem } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ContentRenderer } from "@/components/content/content-renderer"

type AuthorDetailViewProps = {
  author: AuthorWithContentCount
}

const PAGE_SIZE = 20

export function AuthorDetailView({ author }: AuthorDetailViewProps) {
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
        const response = await fetchAuthorContent(author.id, {
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
        console.error("Failed to load author content", error)
        if (mounted) {
          setContentStatus("error")
        }
      }
    }

    loadContent()

    return () => {
      mounted = false
    }
  }, [author.id])

  // Load more content
  const loadMoreContent = useCallback(async () => {
    if (!contentHasMore || loadingMore || !contentCursor) return

    setLoadingMore(true)
    try {
      const response = await fetchAuthorContent(author.id, {
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
  }, [author.id, contentCursor, contentHasMore, loadingMore])

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

  const handleExternalProfile = () => {
    if (author.profile_url) {
      window.open(author.profile_url, "_blank", "noopener,noreferrer")
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

      {/* Author header card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-full bg-slate-200">
              {author.avatar_url ? (
                <Image
                  src={author.avatar_url}
                  alt={author.display_name}
                  fill
                  className="object-cover"
                  unoptimized
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center">
                  <User className="h-10 w-10 text-slate-400" />
                </div>
              )}
            </div>

            {/* Author info */}
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h1 className="text-2xl font-bold text-slate-900">{author.display_name}</h1>
                  <p className="text-base text-slate-500">{author.handle}</p>
                </div>
                {author.profile_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExternalProfile}
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    View Profile
                  </Button>
                )}
              </div>

              {/* Bio */}
              {author.bio && (
                <p className="mt-3 text-sm leading-relaxed text-slate-700">{author.bio}</p>
              )}

              {/* Stats */}
              <div className="mt-4 flex flex-wrap gap-6 text-sm">
                {author.follower_count !== null && author.follower_count !== undefined && (
                  <div>
                    <span className="font-semibold text-slate-900">
                      {formatNumber(author.follower_count)}
                    </span>
                    <span className="ml-1 text-slate-500">Followers</span>
                  </div>
                )}
                {author.following_count !== null && author.following_count !== undefined && (
                  <div>
                    <span className="font-semibold text-slate-900">
                      {formatNumber(author.following_count)}
                    </span>
                    <span className="ml-1 text-slate-500">Following</span>
                  </div>
                )}
                {contentTotal !== null && (
                  <div>
                    <span className="font-semibold text-slate-900">
                      {formatNumber(contentTotal)}
                    </span>
                    <span className="ml-1 text-slate-500">Items Saved</span>
                  </div>
                )}
                {author.platform && (
                  <div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">
                      {author.platform}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

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
              <p className="text-sm">Failed to load content for this author.</p>
            </CardContent>
          </Card>
        )}

        {!isContentLoading && contentStatus !== "error" && (
          <>
            {content.length > 0 ? (
              <>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {content.map((item) => (
                    <ContentRenderer key={item.id} item={item} />
                  ))}
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
                    No content has been saved from this author yet.
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
