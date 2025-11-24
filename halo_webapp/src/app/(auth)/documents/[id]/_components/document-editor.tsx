"use client"

import { useEffect, useRef, useState } from "react"
import type { ContentItem, DocumentSection, TwitterPlatformMetadata } from "@/lib/api"
import Image from "next/image"
import { GripVertical, MoreVertical, Plus, Trash2, Copy } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

type SelectionContext = {
  text: string
  start: number
  end: number
  sectionIndex: number
}

type DocumentEditorProps = {
  sections: DocumentSection[]
  onSectionsChange: (contents: string[]) => void
  onSelectionChange?: (context: SelectionContext) => void
  onBlurSave?: () => void
  onDropCitation?: (sectionIndex: number, position: number, contentId: number) => void
  onDropEmbeddedContent?: (afterSectionIndex: number, contentId: number) => void
  onCreateSection?: (afterSectionIndex: number) => void
  onDeleteSection?: (sectionIndex: number) => void
  onDuplicateSection?: (sectionIndex: number) => void
  onReorderSection?: (fromIndex: number, toIndex: number) => void
  contentCache?: Record<number, ContentItem>
}

export function DocumentEditor({ sections, onSectionsChange, onSelectionChange, onBlurSave, onDropCitation, onDropEmbeddedContent, onCreateSection, onDeleteSection, onDuplicateSection, onReorderSection, contentCache = {} }: DocumentEditorProps) {
  const [selected, setSelected] = useState<number | null>(null)
  const textareasRef = useRef<Array<HTMLTextAreaElement | null>>([])
  const containerRefs = useRef<Array<HTMLDivElement | null>>([])
  const [dragCaret, setDragCaret] = useState<{
    sectionIndex: number
    position: number
    left: number
    top: number
    height: number
  } | null>(null)
  const [hoveredSection, setHoveredSection] = useState<number | null>(null)
  const [isCanvasHovered, setIsCanvasHovered] = useState(false)
  const [draggedSectionIndex, setDraggedSectionIndex] = useState<number | null>(null)
  const [dropTargetIndex, setDropTargetIndex] = useState<number | null>(null)
  const [embeddingDropTarget, setEmbeddingDropTarget] = useState<number | null>(null)
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    if (selected !== null && selected >= sections.length) {
      setSelected(sections.length ? Math.max(0, sections.length - 1) : null)
    }
    textareasRef.current.forEach((textarea) => {
      if (textarea) autoSize(textarea)
    })
  }, [sections])

  const handleSelect = (event: React.SyntheticEvent<HTMLTextAreaElement>) => {
    if (!onSelectionChange) return
    const target = event.currentTarget as HTMLTextAreaElement
    const start = target.selectionStart ?? 0
    const end = target.selectionEnd ?? start
    const sectionIndex = Number(target.dataset.sectionIndex)
    const sectionText = sections[sectionIndex]?.content ?? ""
    setSelected(sectionIndex)
    onSelectionChange({
      text: sectionText,
      start,
      end,
      sectionIndex,
    })
  }

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget
    const index = Number(target.dataset.sectionIndex)
    const contents = sections.map((s) => s.content)
    contents[index] = target.value
    autoSize(target)
    onSectionsChange(contents)
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget
    const index = Number(target.dataset.sectionIndex)
    const value = target.value
    const start = target.selectionStart ?? value.length
    const end = target.selectionEnd ?? start

    // Cmd/Ctrl + Shift + Backspace deletes the section
    if (event.key === "Backspace" && (event.metaKey || event.ctrlKey) && event.shiftKey) {
      event.preventDefault()
      if (onDeleteSection) {
        onDeleteSection(index)
      }
      return
    }

    // Cmd/Ctrl + Enter creates a new section below
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault()
      if (onCreateSection) {
        onCreateSection(index)
        requestAnimationFrame(() => focusSection(index + 1, "start"))
      }
      return
    }

    if (event.key !== "Enter") return

    // Shift+Enter keeps a single newline inside the section
    if (event.shiftKey) {
      return
    }

    const before = value.slice(0, start)
    const after = value.slice(end)
    const hasDoubleBreakBefore = /\n{2}$/.test(before)
    const hasDoubleBreakAfter = /^\n{2}/.test(after)

    // Require two blank lines (one extra paragraph) to split into a new section
    if (hasDoubleBreakBefore || hasDoubleBreakAfter) {
      event.preventDefault()
      const head = before.replace(/\n+$/, "")
      const tail = after.replace(/^\n+/, "")
      const contents = sections.map((s) => s.content)
      const nextContents = [
        ...contents.slice(0, index),
        head,
        tail,
        ...contents.slice(index + 1),
      ].filter((text, idx, arr) => !(text === "" && idx !== 0 && idx !== arr.length - 1))

      onSectionsChange(nextContents)
      requestAnimationFrame(() => focusSection(index + 1, "start"))
      setSelected(index + 1)
      onSelectionChange?.({ text: tail, start: 0, end: 0, sectionIndex: index + 1 })
      return
    }
  }

  const focusSection = (index: number, cursor: number | "start" | "end" = "start") => {
    const textarea = textareasRef.current[index]
    if (textarea) {
      textarea.focus()
      const length = textarea.value.length
      const position = cursor === "end" ? length : typeof cursor === "number" ? cursor : 0
      textarea.setSelectionRange(position, position)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLTextAreaElement>, sectionIndex: number) => {
    if (!onDropCitation) return
    event.preventDefault()
    const textarea = textareasRef.current[sectionIndex]
    const container = containerRefs.current[sectionIndex]
    if (!textarea || !container) return

    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    rafRef.current = requestAnimationFrame(() => {
      const position = getCaretIndexFromPoint(textarea, event.clientX, event.clientY)
      const caretRect = getCaretRect(textarea, position)
      if (!caretRect) return
      const containerRect = container.getBoundingClientRect()
      setDragCaret({
        sectionIndex,
        position,
        left: caretRect.left - containerRect.left,
        top: caretRect.top - containerRect.top,
        height: caretRect.height,
      })
    })
  }

  const handleDrop = (event: React.DragEvent<HTMLTextAreaElement>, sectionIndex: number) => {
    if (!onDropCitation) return
    event.preventDefault()
    const contentId = Number.parseInt(event.dataTransfer?.getData("application/x-content-id") ?? "", 10)
    if (Number.isNaN(contentId)) return

    const caret = dragCaret?.sectionIndex === sectionIndex ? dragCaret.position : getCaretIndexFromPoint(event.currentTarget, event.clientX, event.clientY)
    setDragCaret(null)
    onDropCitation(sectionIndex, caret, contentId)
  }

  const handleSectionDragStart = (event: React.DragEvent, sectionIndex: number) => {
    try {
      // Safety check: ensure valid section index
      if (sectionIndex < 0 || sectionIndex >= sections.length) return

      setDraggedSectionIndex(sectionIndex)
      event.dataTransfer.effectAllowed = "move"

      // Set a transparent drag image
      const dragImage = document.createElement("div")
      dragImage.style.opacity = "0"
      document.body.appendChild(dragImage)
      event.dataTransfer.setDragImage(dragImage, 0, 0)
      setTimeout(() => {
        if (document.body.contains(dragImage)) {
          document.body.removeChild(dragImage)
        }
      }, 0)
    } catch (error) {
      console.error("Error in handleSectionDragStart:", error)
      setDraggedSectionIndex(null)
    }
  }

  const handleSectionDragOver = (event: React.DragEvent, targetIndex: number) => {
    try {
      if (draggedSectionIndex === null) return

      // Safety check: ensure valid indices
      if (targetIndex < 0 || targetIndex >= sections.length) return
      if (draggedSectionIndex < 0 || draggedSectionIndex >= sections.length) {
        setDraggedSectionIndex(null)
        return
      }

      event.preventDefault()
      event.dataTransfer.dropEffect = "move"

      // Determine if drop should be before or after based on mouse position
      const rect = event.currentTarget.getBoundingClientRect()
      const midpoint = rect.top + rect.height / 2
      const dropIndex = event.clientY < midpoint ? targetIndex : targetIndex + 1

      setDropTargetIndex(dropIndex)
    } catch (error) {
      console.error("Error in handleSectionDragOver:", error)
      setDropTargetIndex(null)
    }
  }

  const handleSectionDrop = (event: React.DragEvent) => {
    try {
      event.preventDefault()

      // Safety checks
      if (draggedSectionIndex === null || dropTargetIndex === null || !onReorderSection) {
        return
      }

      if (draggedSectionIndex < 0 || draggedSectionIndex >= sections.length) {
        return
      }

      if (dropTargetIndex < 0 || dropTargetIndex > sections.length) {
        return
      }

      // Calculate the final index after removal
      let finalIndex = dropTargetIndex
      if (dropTargetIndex > draggedSectionIndex) {
        finalIndex = dropTargetIndex - 1
      }

      // Only reorder if indices are different and valid
      if (finalIndex !== draggedSectionIndex && finalIndex >= 0 && finalIndex < sections.length) {
        onReorderSection(draggedSectionIndex, finalIndex)
      }
    } catch (error) {
      console.error("Error in handleSectionDrop:", error)
    } finally {
      // Always clean up drag state
      setDraggedSectionIndex(null)
      setDropTargetIndex(null)
    }
  }

  const handleSectionDragEnd = () => {
    setDraggedSectionIndex(null)
    setDropTargetIndex(null)
  }

  const handleEmbeddingDragOver = (event: React.DragEvent, afterSectionIndex: number) => {
    if (!onDropEmbeddedContent) return

    // Only handle if we're NOT dragging a section (i.e., dragging content from sources)
    if (draggedSectionIndex !== null) return

    try {
      const contentId = event.dataTransfer?.types?.includes("application/x-content-id")
      if (!contentId) return

      event.preventDefault()
      event.stopPropagation()
      setEmbeddingDropTarget(afterSectionIndex)
    } catch (error) {
      console.error("Error in handleEmbeddingDragOver:", error)
    }
  }

  const handleEmbeddingDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    event.stopPropagation()
    setEmbeddingDropTarget(null)
  }

  const handleEmbeddingDrop = (event: React.DragEvent, afterSectionIndex: number) => {
    if (!onDropEmbeddedContent) return

    try {
      event.preventDefault()
      event.stopPropagation()

      const contentId = Number.parseInt(event.dataTransfer?.getData("application/x-content-id") ?? "", 10)
      if (Number.isNaN(contentId)) return

      setEmbeddingDropTarget(null)
      onDropEmbeddedContent(afterSectionIndex, contentId)
    } catch (error) {
      console.error("Error in handleEmbeddingDrop:", error)
      setEmbeddingDropTarget(null)
    }
  }

  useEffect(() => {
    return () => {
      // Clean up any pending animation frames
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
      // Clean up drag state on unmount
      setDraggedSectionIndex(null)
      setDropTargetIndex(null)
      setEmbeddingDropTarget(null)
      setDragCaret(null)
    }
  }, [])

  const indicatorClass = (index: number) => {
    if (selected !== null && index === selected) {
      return "border-l-4 border-l-sky-500"
    }
    return "border-l-2 border-l-transparent hover:border-l-sky-300 hover:bg-sky-50/50"
  }

  const renderEmbeddedContent = (section: DocumentSection) => {
    if (!section.embedded_content_id) return null
    const item = contentCache[section.embedded_content_id]
    if (!item) {
      return (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-500">
          Loading content...
        </div>
      )
    }

    // Check if this is a tweet with platform metadata
    const isTwitterContent = item.platform_metadata &&
      'author' in item.platform_metadata &&
      'text' in item.platform_metadata

    if (isTwitterContent) {
      return <EmbeddedTweetCard item={item} metadata={item.platform_metadata as TwitterPlatformMetadata} />
    }

    return <EmbeddedSourceCard item={item} />
  }

  // Ensure we always have at least one section to avoid switching between rendering paths
  const displaySections = sections.length > 0 ? sections : [{ content: "", id: undefined, document_id: 0, order_index: 0, title: null, word_count: 0, updated_at: undefined } as DocumentSection]

  return (
    <div
      className="flex flex-col gap-4 max-w-3xl mx-auto w-full"
      onMouseEnter={() => setIsCanvasHovered(true)}
      onMouseLeave={() => setIsCanvasHovered(false)}
    >
      {displaySections.map((section, idx) => (
        <div key={idx}>
          {/* Blue drop line indicator at the beginning (for section reordering) */}
          {idx === 0 && dropTargetIndex === 0 && draggedSectionIndex !== null && (
            <div className="relative h-0.5 my-2">
              <div className="absolute inset-0 bg-blue-500 rounded-full shadow-sm" />
            </div>
          )}

          {/* Invisible drop zone before first section (for embedding content) */}
          {idx === 0 && onDropEmbeddedContent && (
            <div
              className="relative h-2 my-2"
              onDragOver={(e) => handleEmbeddingDragOver(e, -1)}
              onDragLeave={handleEmbeddingDragLeave}
              onDrop={(e) => handleEmbeddingDrop(e, -1)}
            >
              {embeddingDropTarget === -1 && (
                <div className="absolute inset-0 h-0.5 bg-blue-500 rounded-full shadow-sm" />
              )}
            </div>
          )}

          {/* Section */}
          {section.embedded_content_id ? (
            // Embedded content section (tweet or other content)
            <div
              className={`relative px-5 py-4 ${draggedSectionIndex === idx ? "opacity-50" : ""}`}
              onMouseEnter={() => setHoveredSection(idx)}
              onMouseLeave={() => setHoveredSection(null)}
              onDragOver={(e) => handleSectionDragOver(e, idx)}
              onDrop={handleSectionDrop}
              onDragEnd={handleSectionDragEnd}
              onClick={() => {
                setSelected(idx)
                onSelectionChange?.({ text: "", start: 0, end: 0, sectionIndex: idx })
              }}
            >
              {/* Drag handle - visible when hovering canvas */}
              <SectionDragHandle
                visible={isCanvasHovered}
                onDragStart={(e) => handleSectionDragStart(e, idx)}
              />

              {/* Control bar - visible only when selected */}
              {(onCreateSection || onDeleteSection || onDuplicateSection) && (
                <SectionControlBar
                  visible={selected === idx}
                  onAddBelow={() => {
                    onCreateSection?.(idx)
                    requestAnimationFrame(() => focusSection(idx + 1, "start"))
                  }}
                  onDelete={() => onDeleteSection?.(idx)}
                  onDuplicate={() => onDuplicateSection?.(idx)}
                  canDelete={displaySections.length > 1}
                />
              )}

              {renderEmbeddedContent(section)}
            </div>
          ) : (
            // Regular text section
            <div
              ref={(el) => {
                containerRefs.current[idx] = el
              }}
              className={`relative rounded-lg transition-all ${indicatorClass(idx)} ${
                draggedSectionIndex === idx ? "opacity-50" : ""
              }`}
              onClick={() => {
                setSelected(idx)
                onSelectionChange?.({ text: section.content, start: 0, end: 0, sectionIndex: idx })
                focusSection(idx, "end")
              }}
              onMouseEnter={() => setHoveredSection(idx)}
              onMouseLeave={() => setHoveredSection(null)}
              onDragOver={(e) => handleSectionDragOver(e, idx)}
              onDrop={handleSectionDrop}
              onDragEnd={handleSectionDragEnd}
              onDragLeave={() => {
                setDragCaret((current) => (current?.sectionIndex === idx ? null : current))
              }}
            >
              {/* Drag handle - visible when hovering canvas */}
              <SectionDragHandle
                visible={isCanvasHovered}
                onDragStart={(e) => handleSectionDragStart(e, idx)}
              />

              {/* Control bar - visible only when selected */}
              {(onCreateSection || onDeleteSection || onDuplicateSection) && (
                <SectionControlBar
                  visible={selected === idx}
                  onAddBelow={() => {
                    onCreateSection?.(idx)
                    requestAnimationFrame(() => focusSection(idx + 1, "start"))
                  }}
                  onDelete={() => onDeleteSection?.(idx)}
                  onDuplicate={() => onDuplicateSection?.(idx)}
                  canDelete={displaySections.length > 1}
                />
              )}

              {dragCaret?.sectionIndex === idx && (
                <div
                  className="pointer-events-none absolute"
                  style={{
                    left: dragCaret.left,
                    top: dragCaret.top,
                    width: 2,
                    height: dragCaret.height || 18,
                    background: "rgb(14 165 233)",
                    boxShadow: "0 0 0 3px rgba(14,165,233,0.20)",
                    borderRadius: 999,
                    zIndex: 10,
                  }}
                />
              )}
              <textarea
                ref={(el) => {
                  textareasRef.current[idx] = el
              if (el) autoSize(el)
            }}
            data-section-index={idx}
            className="w-full resize-none border-0 bg-transparent px-5 py-4 text-lg leading-8 text-slate-900 placeholder:text-slate-400 outline-none focus:ring-0"
            placeholder={idx === 0 ? "Start typing. Press Enter three times to start a new section." : "Continue writing..."}
            value={section.content}
            onChange={handleChange}
            onSelect={handleSelect}
            onKeyUp={handleSelect}
            onMouseUp={handleSelect}
                onKeyDown={handleKeyDown}
                onBlur={onBlurSave}
                onDragOver={(event) => handleDragOver(event, idx)}
                onDrop={(event) => handleDrop(event, idx)}
              />
            </div>
          )}

          {/* Blue drop line indicator (for section reordering) */}
          {dropTargetIndex === idx + 1 && draggedSectionIndex !== null && (
            <div className="relative h-0.5 my-2">
              <div className="absolute inset-0 bg-blue-500 rounded-full shadow-sm" />
            </div>
          )}

          {/* Invisible drop zone after each section (for embedding content) */}
          {onDropEmbeddedContent && (
            <div
              className="relative h-2 my-2"
              onDragOver={(e) => handleEmbeddingDragOver(e, idx)}
              onDragLeave={handleEmbeddingDragLeave}
              onDrop={(e) => handleEmbeddingDrop(e, idx)}
            >
              {embeddingDropTarget === idx && (
                <div className="absolute inset-0 h-0.5 bg-blue-500 rounded-full shadow-sm" />
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function getCaretIndexFromPoint(textarea: HTMLTextAreaElement, clientX: number, clientY: number): number {
  const value = textarea.value
  if (!value) return 0
  let best = 0
  let smallestDistance = Number.POSITIVE_INFINITY
  for (let i = 0; i <= value.length; i++) {
    const rect = getCaretRect(textarea, i)
    if (!rect) continue
    const dx = rect.left - clientX
    const dy = rect.top - clientY
    const distance = Math.sqrt(dx * dx + dy * dy)
    if (distance < smallestDistance) {
      smallestDistance = distance
      best = i
    }
  }
  return best
}

function getCaretRect(textarea: HTMLTextAreaElement, position: number) {
  const mirror = getMirror(textarea)
  mirror.style.width = `${textarea.clientWidth}px`
  mirror.innerHTML = ""

  const before = document.createTextNode(textarea.value.slice(0, position))
  const marker = document.createElement("span")
  marker.textContent = " "
  const after = document.createTextNode(textarea.value.slice(position))

  mirror.append(before, marker, after)

  const markerRect = marker.getBoundingClientRect()
  const mirrorRect = mirror.getBoundingClientRect()

  const left = markerRect.left - mirrorRect.left
  const top = markerRect.top - mirrorRect.top
  const height = markerRect.height || parseInt(getComputedStyle(textarea).lineHeight || "18", 10)

  return {
    left: textarea.getBoundingClientRect().left + left,
    top: textarea.getBoundingClientRect().top + top - textarea.scrollTop,
    height,
  }
}

function getMirror(textarea: HTMLTextAreaElement) {
  const existing = textarea.dataset.mirrorId && document.getElementById(textarea.dataset.mirrorId)
  if (existing) return existing

  const mirror = document.createElement("div")
  const id = `mirror-${Math.random().toString(36).slice(2)}`
  mirror.id = id
  textarea.dataset.mirrorId = id
  const style = window.getComputedStyle(textarea)
  mirror.style.position = "absolute"
  mirror.style.visibility = "hidden"
  mirror.style.whiteSpace = "pre-wrap"
  mirror.style.wordBreak = "break-word"
  mirror.style.top = "0"
  mirror.style.left = "-9999px"
  mirror.style.width = `${textarea.clientWidth}px`
  mirror.style.font = style.font
  mirror.style.letterSpacing = style.letterSpacing
  mirror.style.padding = style.padding
  mirror.style.border = style.border
  mirror.style.lineHeight = style.lineHeight
  document.body.appendChild(mirror)
  return mirror
}

function autoSize(textarea: HTMLTextAreaElement) {
  textarea.style.height = "auto"
  textarea.style.height = `${textarea.scrollHeight}px`
}

function SectionDragHandle({
  visible,
  onDragStart,
}: {
  visible: boolean
  onDragStart?: (event: React.DragEvent) => void
}) {
  return (
    <div
      className={`absolute -left-10 top-0 h-full w-10 z-10 flex items-start pt-2 transition-opacity ${
        visible ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      <div
        draggable={onDragStart !== undefined}
        onDragStart={onDragStart}
        className="flex h-5 w-5 cursor-grab items-center justify-center rounded text-slate-300 transition hover:text-slate-500 active:cursor-grabbing"
        role="button"
        aria-label="Drag to reorder"
      >
        <GripVertical className="h-3.5 w-3.5" />
      </div>
    </div>
  )
}

function SectionControlBar({
  visible,
  onAddBelow,
  onDelete,
  onDuplicate,
  canDelete,
}: {
  visible: boolean
  onAddBelow: () => void
  onDelete: () => void
  onDuplicate: () => void
  canDelete: boolean
}) {
  return (
    <div
      className={`absolute -top-1 right-2 transition-opacity ${
        visible ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      <div className="flex items-center gap-1 rounded border border-slate-200 bg-white px-1 py-0.5 shadow-sm">
        <button
          type="button"
          onClick={onAddBelow}
          className="flex h-6 w-6 items-center justify-center rounded text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
          aria-label="Add section below"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex h-6 w-6 items-center justify-center rounded text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              aria-label="Section options"
            >
              <MoreVertical className="h-3.5 w-3.5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={onDuplicate}>
              <Copy className="mr-2 h-4 w-4" />
              <span>Duplicate section</span>
              <span className="ml-auto text-xs text-slate-500">⌘D</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={onDelete}
              disabled={!canDelete}
              className="text-red-600 focus:text-red-600"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              <span>Delete section</span>
              <span className="ml-auto text-xs text-slate-500">⌘⇧⌫</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

function EmbeddedTweetCard({ item, metadata }: { item: ContentItem; metadata: TwitterPlatformMetadata }) {
  const { author } = metadata
  const tweetText = item.body || metadata.text

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="relative h-12 w-12 overflow-hidden rounded-full bg-slate-200">
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
          <div className="flex items-start gap-1.5">
            <span className="truncate font-bold text-base leading-tight text-slate-900">
              {author.name}
            </span>
            {author.verified && (
              <svg className="h-5 w-5 flex-shrink-0 text-sky-500" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z" />
              </svg>
            )}
          </div>
          <div className="text-sm text-slate-500">@{author.username}</div>

          {/* Tweet text */}
          <p className="mt-3 whitespace-pre-wrap text-base leading-relaxed text-slate-900">
            {tweetText}
          </p>

          {/* Metrics */}
          {metadata.public_metrics && (
            <div className="mt-3 flex gap-4 text-sm text-slate-500">
              {metadata.public_metrics.like_count > 0 && (
                <span className="font-medium">{metadata.public_metrics.like_count.toLocaleString()} likes</span>
              )}
              {metadata.public_metrics.retweet_count > 0 && (
                <span className="font-medium">{metadata.public_metrics.retweet_count.toLocaleString()} retweets</span>
              )}
              {metadata.public_metrics.reply_count > 0 && (
                <span className="font-medium">{metadata.public_metrics.reply_count.toLocaleString()} replies</span>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

function EmbeddedSourceCard({ item }: { item: ContentItem }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold leading-tight text-slate-900">{item.title}</h3>
        {(item.author || item.published_at) && (
          <p className="text-sm text-slate-500">
            {[item.author, item.published_at ? formatDate(item.published_at) : undefined].filter(Boolean).join(" • ")}
          </p>
        )}
        <p className="text-base leading-relaxed text-slate-700">
          {item.excerpt || item.summary || "No content available."}
        </p>
      </div>
    </article>
  )
}

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
}
