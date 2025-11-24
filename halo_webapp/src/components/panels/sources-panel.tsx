"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { RefreshCcw, Search } from "lucide-react"
import { searchContent, type ContentItem, type TwitterPlatformMetadata } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import Image from "next/image"

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

function TweetCard({ item, metadata }: { item: ContentItem; metadata: TwitterPlatformMetadata }) {
  const { author } = metadata
  const tweetText = item.body || metadata.text

  return (
    <article
      draggable
      className="group cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md active:cursor-grabbing"
      onDragStart={(event) => {
        event.dataTransfer?.setData("application/x-content-id", String(item.id))
        event.dataTransfer?.setData("application/x-content-title", `@${author.username}`)
        event.dataTransfer?.setData("text/plain", tweetText)
        event.dataTransfer?.setDragImage(createDragImage(`@${author.username}`), 0, 0)
      }}
    >
      <div className="flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="relative h-10 w-10 overflow-hidden rounded-full bg-slate-200">
            <Image
              src={author.profile_image_url}
              alt={author.name}
              fill
              className="object-cover"
              unoptimized
            />
          </div>
        </div>

        {/* Tweet content */}
        <div className="min-w-0 flex-1">
          {/* Author info */}
          <div className="flex items-start gap-1">
            <span className="truncate font-semibold text-sm leading-tight text-slate-900">
              {author.name}
            </span>
            {author.verified && (
              <svg className="h-4 w-4 flex-shrink-0 text-sky-500" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z" />
              </svg>
            )}
            <span className="truncate text-sm text-slate-500">
              @{author.username}
            </span>
          </div>

          {/* Tweet text */}
          <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-slate-900">
            {tweetText}
          </p>

          {/* Metrics */}
          {metadata.public_metrics && (
            <div className="mt-2 flex gap-4 text-xs text-slate-500">
              {metadata.public_metrics.like_count > 0 && (
                <span>{metadata.public_metrics.like_count.toLocaleString()} likes</span>
              )}
              {metadata.public_metrics.retweet_count > 0 && (
                <span>{metadata.public_metrics.retweet_count.toLocaleString()} retweets</span>
              )}
              {metadata.public_metrics.reply_count > 0 && (
                <span>{metadata.public_metrics.reply_count.toLocaleString()} replies</span>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

function SourceCard({ item }: { item: ContentItem }) {
  return (
    <article
      draggable
      className="group rounded-lg border border-slate-200 bg-white/80 p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md"
      onDragStart={(event) => {
        event.dataTransfer?.setData("application/x-content-id", String(item.id))
        event.dataTransfer?.setData("application/x-content-title", item.title)
        event.dataTransfer?.setData("text/plain", item.title)
        event.dataTransfer?.setDragImage(createDragImage(item.title), 0, 0)
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <p className="text-sm font-medium leading-5">{item.title}</p>
          {(item.author || item.published_at) && (
            <p className="text-xs text-muted-foreground">
              {[item.author, item.published_at ? formatDate(item.published_at) : undefined].filter(Boolean).join(" • ")}
            </p>
          )}
        </div>
      </div>
      <p className="mt-2 line-clamp-3 text-sm leading-6 text-muted-foreground">{item.excerpt || item.summary || "No excerpt available."}</p>
    </article>
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

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

function createDragImage(title: string) {
  const el = document.createElement("div")
  el.textContent = `Source: ${title}`
  el.style.position = "fixed"
  el.style.top = "0"
  el.style.left = "0"
  el.style.padding = "6px 10px"
  el.style.borderRadius = "8px"
  el.style.background = "rgba(12,74,110,0.9)"
  el.style.color = "white"
  el.style.fontSize = "12px"
  el.style.fontWeight = "600"
  el.style.pointerEvents = "none"
  document.body.appendChild(el)
  setTimeout(() => {
    if (el.parentNode) {
      el.parentNode.removeChild(el)
    }
  }, 0)
  return el
}
