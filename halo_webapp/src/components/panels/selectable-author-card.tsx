"use client"

import Image from "next/image"
import { Check, User } from "lucide-react"
import type { AuthorWithContentCount } from "@/lib/api/authors"

type SelectableAuthorCardProps = {
  author: AuthorWithContentCount
  isSelected: boolean
  onToggle: (id: number) => void
}

export function SelectableAuthorCard({ author, isSelected, onToggle }: SelectableAuthorCardProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(author.id)}
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

      {/* Avatar */}
      <div className={`
        relative h-11 w-11 flex-shrink-0 overflow-hidden rounded-full
        ${isSelected ? "ring-2 ring-sky-300" : "bg-slate-100"}
      `}>
        {author.avatar_url ? (
          <Image
            src={author.avatar_url}
            alt=""
            fill
            className="object-cover"
            unoptimized
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-slate-100">
            <User className="h-5 w-5 text-slate-400" />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1 pr-6">
        <p className={`truncate text-sm font-medium ${isSelected ? "text-sky-900" : "text-slate-900"}`}>
          {author.display_name}
        </p>
        <p className="truncate text-xs text-slate-500">{author.handle}</p>

        {/* Stats row */}
        <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
          {author.follower_count !== null && author.follower_count !== undefined && (
            <span>{formatNumber(author.follower_count)} followers</span>
          )}
          {author.platform && (
            <>
              <span className="text-slate-300">·</span>
              <span className="capitalize">{author.platform}</span>
            </>
          )}
        </div>
      </div>
    </button>
  )
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}
