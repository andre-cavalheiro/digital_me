"use client"

import type { MouseEvent, ReactNode } from "react"
import type { ContentItem } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { ExternalLink } from "lucide-react"

type ContentCardShellProps = {
  item: ContentItem
  externalUrl?: string
  dragTitle: string
  dragText?: string
  children: ReactNode
  className?: string
}

/**
  * Shared wrapper for content cards.
  * Provides consistent styling, drag metadata, and optional external link.
  */
export function ContentCardShell({
  item,
  externalUrl,
  dragTitle,
  dragText,
  children,
  className = "",
}: ContentCardShellProps) {
  const handleExternalLink = (e: MouseEvent) => {
    e.stopPropagation()
    if (externalUrl) {
      window.open(externalUrl, "_blank", "noopener,noreferrer")
    }
  }

  return (
    <article
      draggable
      className={`group relative cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md active:cursor-grabbing ${className}`}
      onDragStart={(event) => {
        const dataTransfer = event.dataTransfer
        if (!dataTransfer) return
        dataTransfer.setData("application/x-content-id", String(item.id))
        dataTransfer.setData("application/x-content-title", dragTitle)
        dataTransfer.setData("text/plain", dragText ?? dragTitle)
        dataTransfer.setDragImage(createDragImage(dragTitle), 0, 0)
      }}
    >
      {externalUrl && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
          onClick={handleExternalLink}
          aria-label="Open in new tab"
        >
          <ExternalLink className="h-4 w-4" />
        </Button>
      )}

      {children}
    </article>
  )
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
