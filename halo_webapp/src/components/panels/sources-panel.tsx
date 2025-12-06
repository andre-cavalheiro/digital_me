"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { RefreshCcw, Search, Sliders } from "lucide-react"
import { searchContent, type ContentItem, type Author, type Collection } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ContentRenderer } from "@/components/content/content-renderer"
import { ActiveFiltersBar } from "./active-filters-bar"
import { SourcesFilterDialog } from "./sources-filter-dialog"
import {
  loadDocumentFilters,
  saveDocumentFilters,
  clearDocumentFilters,
  type SourceFilters,
} from "@/lib/storage/document-filters"
import { fetchAuthorsWithContentCount } from "@/lib/api/authors"
import { fetchCollectionsWithContentCount } from "@/lib/api/collections"

type Props = {
  documentId: number
  selectionText: string
}

type FetchState = "idle" | "loading" | "error"

const MIN_QUERY_LENGTH = 8

export function SourcesPanel({ documentId, selectionText }: Props) {
  const [items, setItems] = useState<ContentItem[]>([])
  const [status, setStatus] = useState<FetchState>("idle")
  const [lastQuery, setLastQuery] = useState("")
  const requestRef = useRef(0)

  // Filter state
  const [selectedAuthorIds, setSelectedAuthorIds] = useState<number[]>([])
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<number[]>([])
  const [filterDialogOpen, setFilterDialogOpen] = useState(false)
  const [authors, setAuthors] = useState<Author[]>([])
  const [collections, setCollections] = useState<Collection[]>([])

  const normalizedQuery = useMemo(
    () => selectionText.trim().replace(/\s+/g, " ").slice(0, 800),
    [selectionText],
  )

  // Load filters from localStorage on mount
  useEffect(() => {
    const saved = loadDocumentFilters(documentId)
    if (saved) {
      setSelectedAuthorIds(saved.authorIds)
      setSelectedCollectionIds(saved.collectionIds)
    }

    // Fetch author and collection details for display
    if (saved && (saved.authorIds.length > 0 || saved.collectionIds.length > 0)) {
      if (saved.authorIds.length > 0) {
        fetchAuthorsWithContentCount({ size: 100 })
          .then((response) => {
            setAuthors(response.items.filter((a) => saved.authorIds.includes(a.id)))
          })
          .catch(console.error)
      }
      if (saved.collectionIds.length > 0) {
        fetchCollectionsWithContentCount({ size: 100 })
          .then((response) => {
            setCollections(response.items.filter((c) => saved.collectionIds.includes(c.id)))
          })
          .catch(console.error)
      }
    }
  }, [documentId])

  const runSearch = useCallback(
    async (query: string) => {
      if (!query) return
      const requestId = ++requestRef.current
      setStatus("loading")
      setLastQuery(query)
      try {
        const results = await searchContent({
          query,
          limit: 20,
          authorIds: selectedAuthorIds.length > 0 ? selectedAuthorIds : undefined,
          collectionIds: selectedCollectionIds.length > 0 ? selectedCollectionIds : undefined,
        })
        if (requestRef.current !== requestId) return
        setItems(results)
        setStatus("idle")
      } catch (error) {
        console.error("Failed to search content", error)
        if (requestRef.current !== requestId) return
        setStatus("error")
      }
    },
    [selectedAuthorIds, selectedCollectionIds],
  )

  useEffect(() => {
    if (normalizedQuery.length < MIN_QUERY_LENGTH) {
      setItems([])
      setStatus("idle")
      setLastQuery("")
      return
    }

    setStatus("loading")
    const handle = setTimeout(() => {
      void runSearch(normalizedQuery)
    }, 450)

    return () => clearTimeout(handle)
  }, [normalizedQuery, documentId, runSearch])

  // Filter handlers
  const handleApplyFilters = (filters: SourceFilters) => {
    setSelectedAuthorIds(filters.authorIds)
    setSelectedCollectionIds(filters.collectionIds)
    saveDocumentFilters(documentId, filters)

    // Fetch details for display
    if (filters.authorIds.length > 0) {
      fetchAuthorsWithContentCount({ size: 100 })
        .then((response) => {
          setAuthors(response.items.filter((a) => filters.authorIds.includes(a.id)))
        })
        .catch(console.error)
    } else {
      setAuthors([])
    }

    if (filters.collectionIds.length > 0) {
      fetchCollectionsWithContentCount({ size: 100 })
        .then((response) => {
          setCollections(response.items.filter((c) => filters.collectionIds.includes(c.id)))
        })
        .catch(console.error)
    } else {
      setCollections([])
    }

    // Re-run search with new filters
    if (normalizedQuery.length >= MIN_QUERY_LENGTH) {
      void runSearch(normalizedQuery)
    }
  }

  const handleRemoveAuthor = (authorId: number) => {
    const newFilters = {
      authorIds: selectedAuthorIds.filter((id) => id !== authorId),
      collectionIds: selectedCollectionIds,
    }
    handleApplyFilters(newFilters)
  }

  const handleRemoveCollection = (collectionId: number) => {
    const newFilters = {
      authorIds: selectedAuthorIds,
      collectionIds: selectedCollectionIds.filter((id) => id !== collectionId),
    }
    handleApplyFilters(newFilters)
  }

  const handleClearAllFilters = () => {
    setSelectedAuthorIds([])
    setSelectedCollectionIds([])
    setAuthors([])
    setCollections([])
    clearDocumentFilters(documentId)

    // Re-run search without filters
    if (normalizedQuery.length >= MIN_QUERY_LENGTH) {
      void runSearch(normalizedQuery)
    }
  }

  const showLoading = status === "loading"
  const showError = status === "error"
  const showEmpty = status === "idle" && items.length === 0 && normalizedQuery.length >= MIN_QUERY_LENGTH
  const totalFilters = selectedAuthorIds.length + selectedCollectionIds.length

  return (
    <div className="flex h-full flex-col">
      <header className="border-b px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold leading-tight">Related Content</h2>
          </div>
          <div className="flex items-center gap-2">
            {status === "loading" && (
              <Badge variant="outline" className="text-[11px]">
                Searching…
              </Badge>
            )}
            <Button
              variant={totalFilters > 0 ? "secondary" : "ghost"}
              size="icon"
              className="relative h-8 w-8"
              onClick={() => setFilterDialogOpen(true)}
              aria-label="Filter sources"
            >
              <Sliders className="h-4 w-4" />
              {totalFilters > 0 && (
                <Badge
                  variant="default"
                  className="absolute -right-1 -top-1 h-5 min-w-[20px] px-1 text-[10px]"
                >
                  {totalFilters}
                </Badge>
              )}
            </Button>
          </div>
        </div>
      </header>

      <ActiveFiltersBar
        authors={authors}
        collections={collections}
        onRemoveAuthor={handleRemoveAuthor}
        onRemoveCollection={handleRemoveCollection}
        onClearAll={handleClearAllFilters}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        <ScrollArea className="h-full">
          <div className="flex min-h-full flex-col gap-3 px-4 py-3 pr-5">
            {normalizedQuery.length < MIN_QUERY_LENGTH && (
              <EmptyPrompt
                icon={<Search className="h-4 w-4" />}
                title="Write a bit more to see suggestions"
                hint="We search once a section has a couple of sentences."
              />
            )}

            {!showLoading && showError && (
              <ErrorState
                onRetry={() => runSearch(normalizedQuery)}
                label={lastQuery ? "Retry search" : "Try again"}
              />
            )}

            {!showLoading && showEmpty && (
              <EmptyPrompt title="No sources found yet" hint="Try adding more detail to this section." />
            )}

            {showLoading && <ListSkeleton />}

            {!showLoading && items.length > 0 && (
              <div className="space-y-3">
                {items.map((item) => (
                  <ContentRenderer key={item.id} item={item} />
                ))}
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      <SourcesFilterDialog
        open={filterDialogOpen}
        onOpenChange={setFilterDialogOpen}
        documentId={documentId}
        selectedAuthorIds={selectedAuthorIds}
        selectedCollectionIds={selectedCollectionIds}
        onApply={handleApplyFilters}
      />
    </div>
  )
}


function EmptyPrompt({ icon, title, hint }: { icon?: React.ReactNode; title: string; hint: string }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-md border border-dashed bg-muted/40 px-3 py-6 text-center text-sm text-muted-foreground">
      {icon && <div className="text-muted-foreground">{icon}</div>}
      <p className="font-medium text-foreground">{title}</p>
      <p className="max-w-[18rem] text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, idx) => (
        <div key={idx} className="rounded-lg border bg-muted/30 p-3">
          <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-3 w-full animate-pulse rounded bg-muted" />
          <div className="mt-1 h-3 w-5/6 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}

function ErrorState({ onRetry, label }: { onRetry: () => void; label: string }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-6 text-center">
      <p className="text-sm font-medium text-destructive">Couldn&apos;t load sources right now.</p>
      <Button size="sm" variant="outline" onClick={onRetry}>
        <RefreshCcw className="mr-2 h-4 w-4" />
        {label}
      </Button>
    </div>
  )
}
