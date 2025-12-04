"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SourcesFilterChip } from "./sources-filter-chip"
import type { Author, Collection } from "@/lib/api/types"

interface ActiveFiltersBarProps {
  authors: Author[]
  collections: Collection[]
  onRemoveAuthor: (id: number) => void
  onRemoveCollection: (id: number) => void
  onClearAll: () => void
}

export function ActiveFiltersBar({
  authors,
  collections,
  onRemoveAuthor,
  onRemoveCollection,
  onClearAll,
}: ActiveFiltersBarProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const totalFilters = authors.length + collections.length

  if (totalFilters === 0) {
    return null
  }

  return (
    <div className="border-b border-slate-200 bg-slate-50 px-4 py-2">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
        >
          <span>
            {authors.length > 0 && `${authors.length} author${authors.length === 1 ? "" : "s"}`}
            {authors.length > 0 && collections.length > 0 && " • "}
            {collections.length > 0 && `${collections.length} collection${collections.length === 1 ? "" : "s"}`}
          </span>
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-6 px-2 text-xs hover:bg-slate-200"
        >
          <X className="mr-1 h-3 w-3" />
          Clear all
        </Button>
      </div>

      {isExpanded && (
        <div className="mt-2 flex flex-wrap gap-2">
          {authors.map((author) => (
            <SourcesFilterChip
              key={`author-${author.id}`}
              id={author.id}
              label={author.display_name}
              type="author"
              onRemove={onRemoveAuthor}
            />
          ))}
          {collections.map((collection) => (
            <SourcesFilterChip
              key={`collection-${collection.id}`}
              id={collection.id}
              label={collection.name}
              type="collection"
              onRemove={onRemoveCollection}
            />
          ))}
        </div>
      )}
    </div>
  )
}
