"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { Loader2, Search } from "lucide-react"
import { fetchAuthorsWithContentCount, type AuthorWithContentCount } from "@/lib/api/authors"
import { fetchCollectionsWithContentCount, type CollectionWithContentCount } from "@/lib/api/collections"
import { AuthorCard } from "@/components/sources/author-card"
import { CollectionCard } from "@/components/sources/collection-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

type Tab = "authors" | "collections"
type FetchState = "idle" | "loading" | "error"

const PAGE_SIZE = 20

export default function SourcesPage() {
  const [activeTab, setActiveTab] = useState<Tab>("collections")

  // Search state
  const [authorSearchQuery, setAuthorSearchQuery] = useState("")
  const [collectionSearchQuery, setCollectionSearchQuery] = useState("")

  // Authors state
  const [authors, setAuthors] = useState<AuthorWithContentCount[]>([])
  const [authorsStatus, setAuthorsStatus] = useState<FetchState>("idle")
  const [authorsCursor, setAuthorsCursor] = useState<string | null>(null)
  const [authorsHasMore, setAuthorsHasMore] = useState(true)
  const [loadingMoreAuthors, setLoadingMoreAuthors] = useState(false)
  const [authorsTotal, setAuthorsTotal] = useState<number | null>(null)

  // Collections state
  const [collections, setCollections] = useState<CollectionWithContentCount[]>([])
  const [collectionsStatus, setCollectionsStatus] = useState<FetchState>("idle")
  const [collectionsCursor, setCollectionsCursor] = useState<string | null>(null)
  const [collectionsHasMore, setCollectionsHasMore] = useState(true)
  const [loadingMoreCollections, setLoadingMoreCollections] = useState(false)
  const [collectionsTotal, setCollectionsTotal] = useState<number | null>(null)

  // Refs for infinite scroll
  const authorsSentinelRef = useRef<HTMLDivElement>(null)
  const collectionsSentinelRef = useRef<HTMLDivElement>(null)
  const authorsObserverRef = useRef<IntersectionObserver | null>(null)
  const collectionsObserverRef = useRef<IntersectionObserver | null>(null)

  // Load initial authors (with search support and debouncing)
  useEffect(() => {
    let mounted = true

    setAuthorsStatus("loading")
    setAuthors([])
    setAuthorsCursor(null)
    setAuthorsHasMore(true)

    const timer = setTimeout(() => {
      const loadAuthors = async () => {
        try {
          const response = await fetchAuthorsWithContentCount({
            size: PAGE_SIZE,
            includeTotal: true,
            sortBy: "display_name",
            sortOrder: "asc",
            search: authorSearchQuery || undefined,
          })
          if (mounted) {
            setAuthors(response.items)
            setAuthorsCursor(response.nextCursor)
            setAuthorsHasMore(!!response.nextCursor)
            setAuthorsTotal(response.total ?? null)
            setAuthorsStatus("idle")
          }
        } catch (error) {
          console.error("Failed to load authors", error)
          if (mounted) {
            setAuthorsStatus("error")
          }
        }
      }

      loadAuthors()
    }, 300)

    return () => {
      mounted = false
      clearTimeout(timer)
    }
  }, [authorSearchQuery])

  // Load initial collections (with search support and debouncing)
  useEffect(() => {
    let mounted = true

    setCollectionsStatus("loading")
    setCollections([])
    setCollectionsCursor(null)
    setCollectionsHasMore(true)

    const timer = setTimeout(() => {
      const loadCollections = async () => {
        try {
          const response = await fetchCollectionsWithContentCount({
            size: PAGE_SIZE,
            includeTotal: true,
            sortBy: "name",
            sortOrder: "asc",
            search: collectionSearchQuery || undefined,
          })
          if (mounted) {
            setCollections(response.items)
            setCollectionsCursor(response.nextCursor)
            setCollectionsHasMore(!!response.nextCursor)
            setCollectionsTotal(response.total ?? null)
            setCollectionsStatus("idle")
          }
        } catch (error) {
          console.error("Failed to load collections", error)
          if (mounted) {
            setCollectionsStatus("error")
          }
        }
      }

      loadCollections()
    }, 300)

    return () => {
      mounted = false
      clearTimeout(timer)
    }
  }, [collectionSearchQuery])

  // Load more authors
  const loadMoreAuthors = useCallback(async () => {
    if (!authorsHasMore || loadingMoreAuthors || !authorsCursor) return

    setLoadingMoreAuthors(true)
    try {
      const response = await fetchAuthorsWithContentCount({
        size: PAGE_SIZE,
        cursor: authorsCursor,
        sortBy: "display_name",
        sortOrder: "asc",
        search: authorSearchQuery || undefined,
      })
      setAuthors((prev) => [...prev, ...response.items])
      setAuthorsCursor(response.nextCursor)
      setAuthorsHasMore(!!response.nextCursor)
    } catch (error) {
      console.error("Failed to load more authors", error)
    } finally {
      setLoadingMoreAuthors(false)
    }
  }, [authorsCursor, authorsHasMore, loadingMoreAuthors, authorSearchQuery])

  // Load more collections
  const loadMoreCollections = useCallback(async () => {
    if (!collectionsHasMore || loadingMoreCollections || !collectionsCursor) return

    setLoadingMoreCollections(true)
    try {
      const response = await fetchCollectionsWithContentCount({
        size: PAGE_SIZE,
        cursor: collectionsCursor,
        sortBy: "name",
        sortOrder: "asc",
        search: collectionSearchQuery || undefined,
      })
      setCollections((prev) => [...prev, ...response.items])
      setCollectionsCursor(response.nextCursor)
      setCollectionsHasMore(!!response.nextCursor)
    } catch (error) {
      console.error("Failed to load more collections", error)
    } finally {
      setLoadingMoreCollections(false)
    }
  }, [collectionsCursor, collectionsHasMore, loadingMoreCollections, collectionSearchQuery])

  // Setup IntersectionObserver for authors infinite scroll
  useEffect(() => {
    if (!authorsSentinelRef.current || authorsStatus !== "idle" || activeTab !== "authors") return

    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      if (entry.isIntersecting && authorsHasMore && !loadingMoreAuthors) {
        loadMoreAuthors()
      }
    }

    authorsObserverRef.current = new IntersectionObserver(handleIntersection, {
      threshold: 0.1,
      rootMargin: "100px",
    })

    authorsObserverRef.current.observe(authorsSentinelRef.current)

    return () => {
      if (authorsObserverRef.current) {
        authorsObserverRef.current.disconnect()
      }
    }
  }, [authorsStatus, authorsHasMore, loadMoreAuthors, loadingMoreAuthors, activeTab])

  // Setup IntersectionObserver for collections infinite scroll
  useEffect(() => {
    if (!collectionsSentinelRef.current || collectionsStatus !== "idle" || activeTab !== "collections") return

    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      if (entry.isIntersecting && collectionsHasMore && !loadingMoreCollections) {
        loadMoreCollections()
      }
    }

    collectionsObserverRef.current = new IntersectionObserver(handleIntersection, {
      threshold: 0.1,
      rootMargin: "100px",
    })

    collectionsObserverRef.current.observe(collectionsSentinelRef.current)

    return () => {
      if (collectionsObserverRef.current) {
        collectionsObserverRef.current.disconnect()
      }
    }
  }, [collectionsStatus, collectionsHasMore, loadMoreCollections, loadingMoreCollections, activeTab])

  const handleRetryAuthors = async () => {
    setAuthorsStatus("loading")
    try {
      const response = await fetchAuthorsWithContentCount({
        size: PAGE_SIZE,
        includeTotal: true,
        sortBy: "display_name",
        sortOrder: "asc",
        search: authorSearchQuery || undefined,
      })
      setAuthors(response.items)
      setAuthorsCursor(response.nextCursor)
      setAuthorsHasMore(!!response.nextCursor)
      setAuthorsTotal(response.total ?? null)
      setAuthorsStatus("idle")
    } catch (error) {
      console.error("Failed to retry loading authors", error)
      setAuthorsStatus("error")
    }
  }

  const handleRetryCollections = async () => {
    setCollectionsStatus("loading")
    try {
      const response = await fetchCollectionsWithContentCount({
        size: PAGE_SIZE,
        includeTotal: true,
        sortBy: "name",
        sortOrder: "asc",
        search: collectionSearchQuery || undefined,
      })
      setCollections(response.items)
      setCollectionsCursor(response.nextCursor)
      setCollectionsHasMore(!!response.nextCursor)
      setCollectionsTotal(response.total ?? null)
      setCollectionsStatus("idle")
    } catch (error) {
      console.error("Failed to retry loading collections", error)
      setCollectionsStatus("error")
    }
  }

  const isAuthorsLoading = authorsStatus === "loading" && authors.length === 0
  const isCollectionsLoading = collectionsStatus === "loading" && collections.length === 0

  return (
    <div className="flex h-full flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">Sources</h1>
        <p className="text-sm text-muted-foreground">Browse your library of authors and collections</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("collections")}
          className={`relative px-4 py-2 text-sm font-medium transition ${
            activeTab === "collections"
              ? "text-sky-600"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Collections
          {collectionsTotal !== null && collectionsTotal > 0 && (
            <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs">
              {collectionsTotal}
            </span>
          )}
          {activeTab === "collections" && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-600" />
          )}
        </button>
        <button
          onClick={() => setActiveTab("authors")}
          className={`relative px-4 py-2 text-sm font-medium transition ${
            activeTab === "authors"
              ? "text-sky-600"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Authors
          {authorsTotal !== null && authorsTotal > 0 && (
            <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs">
              {authorsTotal}
            </span>
          )}
          {activeTab === "authors" && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-600" />
          )}
        </button>
      </div>

      {/* Authors Tab */}
      {activeTab === "authors" && (
        <>
          {/* Search bar */}
          <div className="mb-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search authors (by handle)..."
                value={authorSearchQuery}
                onChange={(e) => setAuthorSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            {!isAuthorsLoading && authorsTotal !== null && (
              <div className="mt-2 text-xs text-slate-500">
                {authorSearchQuery && (
                  <span>{authors.length} results · </span>
                )}
                <span>{authorsTotal.toLocaleString()} total</span>
              </div>
            )}
          </div>

          {isAuthorsLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          )}

          {authorsStatus === "error" && !isAuthorsLoading && (
            <Card className="border-destructive/20 bg-destructive/5 text-destructive">
              <CardHeader>
                <CardTitle>Unable to load authors</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4 text-sm">Check your connection or try again.</p>
                <Button variant="outline" onClick={handleRetryAuthors}>
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {!isAuthorsLoading && authorsStatus !== "error" && (
            <>
              {authors.length > 0 ? (
                <>
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {authors.map((author) => (
                      <AuthorCard key={author.id} author={author} />
                    ))}
                  </div>

                  {/* Infinite scroll sentinel */}
                  <div ref={authorsSentinelRef} className="flex justify-center py-4">
                    {loadingMoreAuthors && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading more...
                      </div>
                    )}
                    {!loadingMoreAuthors && authorsHasMore && (
                      <Button variant="outline" onClick={loadMoreAuthors}>
                        Load More
                      </Button>
                    )}
                  </div>
                </>
              ) : (
                <Card className="border-dashed text-muted-foreground">
                  <CardHeader>
                    <CardTitle>No authors yet</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">
                      Authors will appear here once you start importing content from your connected sources.
                    </p>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {/* Collections Tab */}
      {activeTab === "collections" && (
        <>
          {/* Search bar */}
          <div className="mb-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search collections..."
                value={collectionSearchQuery}
                onChange={(e) => setCollectionSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            {!isCollectionsLoading && collectionsTotal !== null && (
              <div className="mt-2 text-xs text-slate-500">
                {collectionSearchQuery && (
                  <span>{collections.length} results · </span>
                )}
                <span>{collectionsTotal.toLocaleString()} total</span>
              </div>
            )}
          </div>

          {isCollectionsLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          )}

          {collectionsStatus === "error" && !isCollectionsLoading && (
            <Card className="border-destructive/20 bg-destructive/5 text-destructive">
              <CardHeader>
                <CardTitle>Unable to load collections</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4 text-sm">Check your connection or try again.</p>
                <Button variant="outline" onClick={handleRetryCollections}>
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {!isCollectionsLoading && collectionsStatus !== "error" && (
            <>
              {collections.length > 0 ? (
                <>
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {collections.map((collection) => (
                      <CollectionCard key={collection.id} collection={collection} />
                    ))}
                  </div>

                  {/* Infinite scroll sentinel */}
                  <div ref={collectionsSentinelRef} className="flex justify-center py-4">
                    {loadingMoreCollections && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading more...
                      </div>
                    )}
                    {!loadingMoreCollections && collectionsHasMore && (
                      <Button variant="outline" onClick={loadMoreCollections}>
                        Load More
                      </Button>
                    )}
                  </div>
                </>
              ) : (
                <Card className="border-dashed text-muted-foreground">
                  <CardHeader>
                    <CardTitle>No collections yet</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">
                      Collections like bookmark folders will appear here once you import them from your connected sources.
                    </p>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
