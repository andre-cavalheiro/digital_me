"use client"

import { Search, X, Loader2 } from "lucide-react"
import { Input } from "@/components/ui/input"

type ContentSearchInputProps = {
  value: string
  onChange: (value: string) => void
  onClear: () => void
  onSearch: () => void
  isSearching: boolean
}

export function ContentSearchInput({ value, onChange, onClear, onSearch, isSearching }: ContentSearchInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      onSearch()
    }
  }

  return (
    <div className="relative">
      <div className="relative flex items-center">
        <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search your content (press Enter to search)..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="pl-9 pr-9"
        />
        <div className="absolute right-3 flex items-center">
          {isSearching ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : value ? (
            <button
              onClick={onClear}
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
