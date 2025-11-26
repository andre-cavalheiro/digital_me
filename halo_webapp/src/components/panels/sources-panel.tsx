"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { RefreshCcw, Search } from "lucide-react"
import { searchContent, type ContentItem, type TwitterPlatformMetadata } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { TweetCard, SourceCard } from "@/components/content/content-cards"

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

  const normalizedQuery = useMemo(
    () => selectionText.trim().replace(/\s+/g, " ").slice(0, 800),
    [selectionText],
  )

  const runSearch = useCallback(async (query: string) => {
    if (!query) return
    const requestId = ++requestRef.current
    setStatus("loading")
    setLastQuery(query)
    try {
      const results = await searchContent({ query, limit: 20 })
      if (requestRef.current !== requestId) return
      setItems(results)
      setStatus("idle")
    } catch (error) {
      console.error("Failed to search content", error)
      if (requestRef.current !== requestId) return
      setStatus("error")
    }
  }, [])

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

  const showLoading = status === "loading"
  const showError = status === "error"
  const showEmpty = status === "idle" && items.length === 0 && normalizedQuery.length >= MIN_QUERY_LENGTH

  return (
    <div className="flex h-full flex-col">
      <header className="border-b px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold leading-tight">Related Content</h2>
          </div>
          {status === "loading" && (
            <Badge variant="outline" className="text-[11px]">
              Searching…
            </Badge>
          )}
        </div>
      </header>

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
                {items.map((item) => {
                  // Check if this is a tweet with platform metadata
                  const isTwitterContent = item.platform_metadata &&
                    'author' in item.platform_metadata &&
                    'text' in item.platform_metadata

                  if (isTwitterContent) {
                    return <TweetCard key={item.id} item={item} metadata={item.platform_metadata as TwitterPlatformMetadata} />
                  }

                  return <SourceCard key={item.id} item={item} />
                })}
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
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
