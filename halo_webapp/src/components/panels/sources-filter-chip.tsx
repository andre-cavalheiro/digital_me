"use client"

import { X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface SourcesFilterChipProps {
  id: number
  label: string
  type: "author" | "collection"
  onRemove: (id: number) => void
}

export function SourcesFilterChip({ id, label, type, onRemove }: SourcesFilterChipProps) {
  return (
    <Badge variant="secondary" className="flex items-center gap-1 pr-1">
      <span className="text-xs">{label}</span>
      <Button
        variant="ghost"
        size="icon"
        className="h-4 w-4 rounded-full hover:bg-slate-300"
        onClick={() => onRemove(id)}
        aria-label={`Remove ${type} filter: ${label}`}
      >
        <X className="h-3 w-3" />
      </Button>
    </Badge>
  )
}
