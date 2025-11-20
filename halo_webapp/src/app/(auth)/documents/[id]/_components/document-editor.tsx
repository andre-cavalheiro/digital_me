"use client"

import { useEffect, useRef, useState } from "react"
import type { DocumentSection } from "@/lib/api"

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
}

export function DocumentEditor({ sections, onSectionsChange, onSelectionChange, onBlurSave, onDropCitation }: DocumentEditorProps) {
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
    if (event.key !== "Enter") return
    const target = event.currentTarget
    const index = Number(target.dataset.sectionIndex)
    const value = target.value
    const start = target.selectionStart ?? value.length
    const end = target.selectionEnd ?? start

    // Shift+Enter keeps a single newline inside the section
    if (event.shiftKey) {
      return
    }

    const before = value.slice(0, start)
    const after = value.slice(end)
    const prevChar = before.at(-1)
    const nextChar = after.at(0)

    // If this Enter would create a double newline, split into a new section
    if (prevChar === "\n" || nextChar === "\n") {
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

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const indicatorClass = (index: number) => {
    if (selected !== null && index === selected) {
      return "border-l-4 border-l-sky-500"
    }
    return "border-l-2 border-l-transparent hover:border-l-sky-300 hover:bg-sky-50/50"
  }

  // Ensure we always have at least one section to avoid switching between rendering paths
  const displaySections = sections.length > 0 ? sections : [{ content: "", id: undefined, document_id: 0, order_index: 0, title: null, word_count: 0, updated_at: undefined } as DocumentSection]

  return (
    <div className="flex h-full flex-col gap-3 p-3">
      {displaySections.map((section, idx) => (
        <div
          key={idx}
          ref={(el) => {
            containerRefs.current[idx] = el
          }}
          className={`relative rounded-lg transition ${indicatorClass(idx)}`}
          onClick={() => {
            setSelected(idx)
            onSelectionChange?.({ text: section.content, start: 0, end: 0, sectionIndex: idx })
            focusSection(idx, "end")
          }}
          onDragLeave={() => {
            setDragCaret((current) => (current?.sectionIndex === idx ? null : current))
          }}
        >
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
            className="w-full resize-none border-0 bg-transparent px-4 py-3 text-base leading-7 text-foreground outline-none focus:ring-0"
            placeholder={idx === 0 ? "Start typing. Press Enter twice to start a new section." : "Continue writing..."}
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
