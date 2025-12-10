"use client"

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { Search, Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { SelectableAuthorCard } from "./selectable-author-card"
import { SelectableCollectionCard } from "./selectable-collection-card"
import {
  fetchAuthorsWithContentCount,
  fetchAuthorsByIds,
  type AuthorWithContentCount,
} from "@/lib/api/authors"
import {
  fetchCollectionsWithContentCount,
  fetchCollectionsByIds,
  type CollectionWithContentCount,
} from "@/lib/api/collections"
import type { SourceFilters } from "@/lib/storage/document-filters"

const PAGE_SIZE = 30

interface SourcesFilterDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  documentId: number
  selectedAuthorIds: number[]
  selectedCollectionIds: number[]
  onApply: (filters: SourceFilters) => void
}

export function SourcesFilterDialog({
  open,
  onOpenChange,
  documentId,
  selectedAuthorIds,
  selectedCollectionIds,
  onApply,
}: SourcesFilterDialogProps) {
  // Pre-selected items (fetched by ID to ensure they're always available)
  const [preSelectedAuthors, setPreSelectedAuthors] = useState<AuthorWithContentCount[]>([])
  const [preSelectedCollections, setPreSelectedCollections] = useState<CollectionWithContentCount[]>([])

  // Paginated items from normal list
  const [paginatedAuthors, setPaginatedAuthors] = useState<AuthorWithContentCount[]>([])
  const [authorsNextCursor, setAuthorsNextCursor] = useState<string | null>(null)
  const [authorsTotal, setAuthorsTotal] = useState<number | null>(null)
  const [isLoadingAuthors, setIsLoadingAuthors] = useState(false)
  const [isLoadingMoreAuthors, setIsLoadingMoreAuthors] = useState(false)

  const [paginatedCollections, setPaginatedCollections] = useState<CollectionWithContentCount[]>([])
  const [collectionsNextCursor, setCollectionsNextCursor] = useState<string | null>(null)
  const [collectionsTotal, setCollectionsTotal] = useState<number | null>(null)
  const [isLoadingCollections, setIsLoadingCollections] = useState(false)
  const [isLoadingMoreCollections, setIsLoadingMoreCollections] = useState(false)

  // Selection state
  const [tempAuthorIds, setTempAuthorIds] = useState<number[]>(selectedAuthorIds)
  const [tempCollectionIds, setTempCollectionIds] = useState<number[]>(selectedCollectionIds)

  // Search state
  const [authorSearchQuery, setAuthorSearchQuery] = useState("")
  const [collectionSearchQuery, setCollectionSearchQuery] = useState("")

  // Refs for infinite scroll
  const authorsLoaderRef = useRef<HTMLDivElement>(null)
  const collectionsLoaderRef = useRef<HTMLDivElement>(null)

  // Store the initial selected IDs when modal opens (for pinning to top)
  const initialAuthorIdsRef = useRef<Set<number>>(new Set())
  const initialCollectionIdsRef = useRef<Set<number>>(new Set())

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setTempAuthorIds(selectedAuthorIds)
      setTempCollectionIds(selectedCollectionIds)
      setAuthorSearchQuery("")
      setCollectionSearchQuery("")
      // Reset pagination
      setPaginatedAuthors([])
      setAuthorsNextCursor(null)
      setAuthorsTotal(null)
      setPaginatedCollections([])
      setCollectionsNextCursor(null)
      setCollectionsTotal(null)
      // Capture initial selections for pinning
      initialAuthorIdsRef.current = new Set(selectedAuthorIds)
      initialCollectionIdsRef.current = new Set(selectedCollectionIds)
    }
  }, [open, selectedAuthorIds, selectedCollectionIds])

  // Fetch pre-selected authors by ID when modal opens
  useEffect(() => {
    if (!open) return
    if (selectedAuthorIds.length === 0) {
      setPreSelectedAuthors([])
      return
    }

    fetchAuthorsByIds(selectedAuthorIds)
      .then(setPreSelectedAuthors)
      .catch((error) => {
        console.error("Failed to fetch pre-selected authors", error)
        setPreSelectedAuthors([])
      })
  }, [open, selectedAuthorIds])

  // Fetch pre-selected collections by ID when modal opens
  useEffect(() => {
    if (!open) return
    if (selectedCollectionIds.length === 0) {
      setPreSelectedCollections([])
      return
    }

    fetchCollectionsByIds(selectedCollectionIds)
      .then(setPreSelectedCollections)
      .catch((error) => {
        console.error("Failed to fetch pre-selected collections", error)
        setPreSelectedCollections([])
      })
  }, [open, selectedCollectionIds])

  // Fetch paginated authors (initial load or search change)
  useEffect(() => {
    if (!open) return

    setIsLoadingAuthors(true)
    setPaginatedAuthors([])
    setAuthorsNextCursor(null)

    const timer = setTimeout(() => {
      fetchAuthorsWithContentCount({
        size: PAGE_SIZE,
        sortBy: "display_name",
        sortOrder: "asc",
        search: authorSearchQuery || undefined,
        includeTotal: true,
      })
        .then((response) => {
          setPaginatedAuthors(response.items)
          setAuthorsNextCursor(response.nextCursor)
          setAuthorsTotal(response.total ?? null)
        })
        .catch((error) => {
          console.error("Failed to fetch authors", error)
          setPaginatedAuthors([])
          setAuthorsTotal(null)
        })
        .finally(() => setIsLoadingAuthors(false))
    }, 300)

    return () => clearTimeout(timer)
  }, [open, authorSearchQuery])

  // Fetch paginated collections (initial load or search change)
  useEffect(() => {
    if (!open) return

    setIsLoadingCollections(true)
    setPaginatedCollections([])
    setCollectionsNextCursor(null)

    const timer = setTimeout(() => {
      fetchCollectionsWithContentCount({
        size: PAGE_SIZE,
        sortBy: "name",
        sortOrder: "asc",
        search: collectionSearchQuery || undefined,
        includeTotal: true,
      })
        .then((response) => {
          setPaginatedCollections(response.items)
          setCollectionsNextCursor(response.nextCursor)
          setCollectionsTotal(response.total ?? null)
        })
        .catch((error) => {
          console.error("Failed to fetch collections", error)
          setPaginatedCollections([])
          setCollectionsTotal(null)
        })
        .finally(() => setIsLoadingCollections(false))
    }, 300)

    return () => clearTimeout(timer)
  }, [open, collectionSearchQuery])

  // Load more authors
  const loadMoreAuthors = useCallback(async () => {
    if (!authorsNextCursor || isLoadingMoreAuthors) return

    setIsLoadingMoreAuthors(true)
    try {
      const response = await fetchAuthorsWithContentCount({
        size: PAGE_SIZE,
        cursor: authorsNextCursor,
        sortBy: "display_name",
        sortOrder: "asc",
        search: authorSearchQuery || undefined,
      })
      setPaginatedAuthors((prev) => [...prev, ...response.items])
      setAuthorsNextCursor(response.nextCursor)
    } catch (error) {
      console.error("Failed to load more authors", error)
    } finally {
      setIsLoadingMoreAuthors(false)
    }
  }, [authorsNextCursor, isLoadingMoreAuthors, authorSearchQuery])

  // Load more collections
  const loadMoreCollections = useCallback(async () => {
    if (!collectionsNextCursor || isLoadingMoreCollections) return

    setIsLoadingMoreCollections(true)
    try {
      const response = await fetchCollectionsWithContentCount({
        size: PAGE_SIZE,
        cursor: collectionsNextCursor,
        sortBy: "name",
        sortOrder: "asc",
        search: collectionSearchQuery || undefined,
      })
      setPaginatedCollections((prev) => [...prev, ...response.items])
      setCollectionsNextCursor(response.nextCursor)
    } catch (error) {
      console.error("Failed to load more collections", error)
    } finally {
      setIsLoadingMoreCollections(false)
    }
  }, [collectionsNextCursor, isLoadingMoreCollections, collectionSearchQuery])

  // Intersection observer for authors infinite scroll
  useEffect(() => {
    const loader = authorsLoaderRef.current
    if (!loader) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && authorsNextCursor && !isLoadingMoreAuthors) {
          loadMoreAuthors()
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(loader)
    return () => observer.disconnect()
  }, [authorsNextCursor, isLoadingMoreAuthors, loadMoreAuthors])

  // Intersection observer for collections infinite scroll
  useEffect(() => {
    const loader = collectionsLoaderRef.current
    if (!loader) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && collectionsNextCursor && !isLoadingMoreCollections) {
          loadMoreCollections()
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(loader)
    return () => observer.disconnect()
  }, [collectionsNextCursor, isLoadingMoreCollections, loadMoreCollections])

  // Merge pre-selected authors with paginated authors (pre-selected first, deduplicated)
  const mergedAuthors = useMemo(() => {
    // When searching, don't include pre-selected items (they might not match the search)
    if (authorSearchQuery) {
      return paginatedAuthors
    }

    const preSelectedIds = new Set(preSelectedAuthors.map((a) => a.id))
    const filteredPaginated = paginatedAuthors.filter((a) => !preSelectedIds.has(a.id))
    return [...preSelectedAuthors, ...filteredPaginated]
  }, [preSelectedAuthors, paginatedAuthors, authorSearchQuery])

  // Merge pre-selected collections with paginated collections
  const mergedCollections = useMemo(() => {
    // When searching, don't include pre-selected items
    if (collectionSearchQuery) {
      return paginatedCollections
    }

    const preSelectedIds = new Set(preSelectedCollections.map((c) => c.id))
    const filteredPaginated = paginatedCollections.filter((c) => !preSelectedIds.has(c.id))
    return [...preSelectedCollections, ...filteredPaginated]
  }, [preSelectedCollections, paginatedCollections, collectionSearchQuery])

  const handleToggleAuthor = (id: number) => {
    setTempAuthorIds((prev) => (prev.includes(id) ? prev.filter((aid) => aid !== id) : [...prev, id]))
  }

  const handleToggleCollection = (id: number) => {
    setTempCollectionIds((prev) => (prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]))
  }

  const handleSelectAllAuthors = () => {
    // Select all currently loaded authors
    setTempAuthorIds((prev) => {
      const newIds = new Set(prev)
      mergedAuthors.forEach((a) => newIds.add(a.id))
      return Array.from(newIds)
    })
  }

  const handleClearAllAuthors = () => {
    setTempAuthorIds([])
  }

  const handleSelectAllCollections = () => {
    // Select all currently loaded collections
    setTempCollectionIds((prev) => {
      const newIds = new Set(prev)
      mergedCollections.forEach((c) => newIds.add(c.id))
      return Array.from(newIds)
    })
  }

  const handleClearAllCollections = () => {
    setTempCollectionIds([])
  }

  const handleClearAll = () => {
    setTempAuthorIds([])
    setTempCollectionIds([])
  }

  const handleApply = () => {
    onApply({
      authorIds: tempAuthorIds,
      collectionIds: tempCollectionIds,
    })
    onOpenChange(false)
  }

  const handleCancel = () => {
    setTempAuthorIds(selectedAuthorIds)
    setTempCollectionIds(selectedCollectionIds)
    onOpenChange(false)
  }

  const totalSelected = tempAuthorIds.length + tempCollectionIds.length
  const hasChanges =
    JSON.stringify([...tempAuthorIds].sort()) !== JSON.stringify([...selectedAuthorIds].sort()) ||
    JSON.stringify([...tempCollectionIds].sort()) !== JSON.stringify([...selectedCollectionIds].sort())

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] max-h-[700px] w-full max-w-[800px] flex-col gap-0 p-0">
        {/* Header - Fixed */}
        <DialogHeader className="border-b px-6 py-4">
          <DialogTitle>Configure Sources</DialogTitle>
          <DialogDescription>
            Choose which authors and collections to include in related content searches.
          </DialogDescription>
        </DialogHeader>

        {/* Tabs - Takes remaining space */}
        <Tabs defaultValue="authors" className="flex flex-1 flex-col overflow-hidden">
          <TabsList className="mx-6 mt-4 grid w-auto grid-cols-2">
            <TabsTrigger value="authors">
              Authors {tempAuthorIds.length > 0 && `(${tempAuthorIds.length})`}
            </TabsTrigger>
            <TabsTrigger value="collections">
              Collections {tempCollectionIds.length > 0 && `(${tempCollectionIds.length})`}
            </TabsTrigger>
          </TabsList>

          {/* Authors Tab */}
          <TabsContent value="authors" className="flex flex-1 flex-col overflow-hidden px-6 pb-0 pt-4">
            {/* Search bar - Fixed */}
            <div className="mb-4 space-y-3">
              <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="text"
                    placeholder="Search authors (by handle)..."
                    value={authorSearchQuery}
                    onChange={(e) => setAuthorSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSelectAllAuthors}
                    disabled={isLoadingAuthors || mergedAuthors.length === 0}
                  >
                    Select all
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClearAllAuthors}
                    disabled={tempAuthorIds.length === 0}
                  >
                    Clear
                  </Button>
                </div>
              </div>

              {!isLoadingAuthors && (
                <div className="text-xs text-slate-500">
                  {tempAuthorIds.length > 0 && (
                    <span className="font-medium text-sky-600">{tempAuthorIds.length} selected</span>
                  )}
                  {tempAuthorIds.length > 0 && authorsTotal !== null && " · "}
                  {authorsTotal !== null && (
                    <span>{authorsTotal.toLocaleString()} total</span>
                  )}
                </div>
              )}
            </div>

            {/* Scrollable grid */}
            <div className="flex-1 overflow-y-auto pb-4">
              {isLoadingAuthors ? (
                <div className="grid grid-cols-2 gap-3">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="flex h-[88px] items-center gap-3 rounded-lg border border-slate-200 p-3">
                      <Skeleton className="h-11 w-11 rounded-full" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                        <Skeleton className="h-3 w-2/3" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : mergedAuthors.length === 0 ? (
                <div className="flex h-[200px] items-center justify-center text-sm text-slate-500">
                  {authorSearchQuery ? "No authors found" : "No authors available"}
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {mergedAuthors.map((author) => (
                    <SelectableAuthorCard
                      key={author.id}
                      author={author}
                      isSelected={tempAuthorIds.includes(author.id)}
                      onToggle={handleToggleAuthor}
                    />
                  ))}
                </div>
              )}

              {/* Infinite scroll loader */}
              {authorsNextCursor && (
                <div ref={authorsLoaderRef} className="flex items-center justify-center py-4">
                  {isLoadingMoreAuthors && (
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading more...
                    </div>
                  )}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Collections Tab */}
          <TabsContent value="collections" className="flex flex-1 flex-col overflow-hidden px-6 pb-0 pt-4">
            {/* Search bar - Fixed */}
            <div className="mb-4 space-y-3">
              <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="text"
                    placeholder="Search collections..."
                    value={collectionSearchQuery}
                    onChange={(e) => setCollectionSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSelectAllCollections}
                    disabled={isLoadingCollections || mergedCollections.length === 0}
                  >
                    Select all
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClearAllCollections}
                    disabled={tempCollectionIds.length === 0}
                  >
                    Clear
                  </Button>
                </div>
              </div>

              {!isLoadingCollections && (
                <div className="text-xs text-slate-500">
                  {tempCollectionIds.length > 0 && (
                    <span className="font-medium text-sky-600">{tempCollectionIds.length} selected</span>
                  )}
                  {tempCollectionIds.length > 0 && collectionsTotal !== null && " · "}
                  {collectionsTotal !== null && (
                    <span>{collectionsTotal.toLocaleString()} total</span>
                  )}
                </div>
              )}
            </div>

            {/* Scrollable grid */}
            <div className="flex-1 overflow-y-auto pb-4">
              {isLoadingCollections ? (
                <div className="grid grid-cols-2 gap-3">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="flex h-[88px] items-center gap-3 rounded-lg border border-slate-200 p-3">
                      <Skeleton className="h-11 w-11 rounded-lg" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : mergedCollections.length === 0 ? (
                <div className="flex h-[200px] items-center justify-center text-sm text-slate-500">
                  {collectionSearchQuery ? "No collections found" : "No collections available"}
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {mergedCollections.map((collection) => (
                    <SelectableCollectionCard
                      key={collection.id}
                      collection={collection}
                      isSelected={tempCollectionIds.includes(collection.id)}
                      onToggle={handleToggleCollection}
                    />
                  ))}
                </div>
              )}

              {/* Infinite scroll loader */}
              {collectionsNextCursor && (
                <div ref={collectionsLoaderRef} className="flex items-center justify-center py-4">
                  {isLoadingMoreCollections && (
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading more...
                    </div>
                  )}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Footer - Fixed */}
        <div className="flex items-center justify-between border-t bg-slate-50 px-6 py-4">
          <Button variant="outline" onClick={handleClearAll} disabled={totalSelected === 0}>
            Clear All
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button onClick={handleApply} disabled={!hasChanges}>
              Apply {totalSelected > 0 && `(${totalSelected})`}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
