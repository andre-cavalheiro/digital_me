"use client"

import { Check, FolderOpen } from "lucide-react"
import type { CollectionWithContentCount } from "@/lib/api/collections"

type SelectableCollectionCardProps = {
  collection: CollectionWithContentCount
  isSelected: boolean
  onToggle: (id: number) => void
}

export function SelectableCollectionCard({ collection, isSelected, onToggle }: SelectableCollectionCardProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(collection.id)}
      className={`
        group relative flex h-[88px] w-full items-center gap-3 rounded-lg border-2 p-3 text-left
        transition-all duration-150 ease-out
        ${isSelected
          ? "border-sky-500 bg-sky-50 ring-2 ring-sky-200"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
        }
      `}
    >
      {/* Checkbox indicator */}
      <div
        className={`
          absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded
          border-2 transition-all duration-150
          ${isSelected
            ? "border-sky-500 bg-sky-500"
            : "border-slate-300 bg-white group-hover:border-slate-400"
          }
        `}
      >
        {isSelected && <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />}
      </div>

      {/* Icon */}
      <div className={`
        flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg
        ${isSelected ? "bg-sky-200" : "bg-sky-100"}
      `}>
        <FolderOpen className={`h-5 w-5 ${isSelected ? "text-sky-700" : "text-sky-600"}`} />
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1 pr-6">
        <p className={`line-clamp-2 text-sm font-medium leading-tight ${isSelected ? "text-sky-900" : "text-slate-900"}`}>
          {collection.name}
        </p>

        {/* Stats row */}
        <div className="mt-1.5 flex items-center gap-2 text-xs text-slate-400">
          {collection.content_count !== undefined && collection.content_count > 0 && (
            <span>{collection.content_count} items</span>
          )}
          {collection.platform && (
            <>
              {collection.content_count !== undefined && collection.content_count > 0 && (
                <span className="text-slate-300">·</span>
              )}
              <span className="capitalize">{collection.platform}</span>
            </>
          )}
          {!collection.content_count && !collection.platform && (
            <span className="capitalize text-slate-400">{collection.type.replace(/_/g, " ")}</span>
          )}
        </div>
      </div>
    </button>
  )
}
