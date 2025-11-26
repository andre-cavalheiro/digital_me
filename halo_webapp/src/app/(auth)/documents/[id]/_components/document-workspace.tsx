"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { createCitation, fetchCitations, fetchContentItem, fetchDocument, fetchDocumentContent, saveDocumentContent, updateDocumentTitle, type Citation, type ContentItem, type Document, type DocumentSection } from "@/lib/api"
import { WorkspaceShell } from "@/components/layout/workspace-shell"
import { SourcesPanel } from "@/components/panels/sources-panel"
import { AssistantPanel } from "@/components/panels/assistant-panel"
import { DocumentEditor } from "./document-editor"
import { Input } from "@/components/ui/input"
import { ArrowLeft, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from "lucide-react"

type Props = {
  documentId: number
}

type FetchState = "idle" | "loading" | "error"
type SaveState = "idle" | "saving" | "error"

const MAX_SELECTION_CONTEXT = 1200

export function DocumentWorkspace({ documentId }: Props) {
  const router = useRouter()
  const [document, setDocument] = useState<Document | null>(null)
  const [sections, setSections] = useState<DocumentSection[]>([])
  const [status, setStatus] = useState<FetchState>("idle")
  const [saveState, setSaveState] = useState<SaveState>("idle")
  const [dirty, setDirty] = useState(false)
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null)
  const [selectionText, setSelectionText] = useState<string>("")
  const [citations, setCitations] = useState<Citation[]>([])
  const [showSources, setShowSources] = useState(true)
  const [showAssistant, setShowAssistant] = useState(true)
  const [leftWidth, setLeftWidth] = useState(320)
  const [rightWidth, setRightWidth] = useState(360)
  const [contentCache, setContentCache] = useState<Record<number, ContentItem>>({})
  const initialLoadRef = useRef(true)
  const debounceRef = useRef<NodeJS.Timeout | null>(null)
  const suppressDirtyRef = useRef(false)
  const [titleValue, setTitleValue] = useState("")
  const [titleSaving, setTitleSaving] = useState(false)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      setStatus("loading")
      try {
        const [doc, docContent, docCitations] = await Promise.all([
          fetchDocument(documentId),
          fetchDocumentContent(documentId),
          fetchCitations(documentId).catch(() => []),
        ])
        if (mounted) {
          setDocument(doc)
          setTitleValue(doc.title)
          suppressDirtyRef.current = true
          setSections(docContent)
          setLastSavedAt(latestUpdatedAt(docContent))
          setCitations(docCitations)
          setStatus("idle")
          setDirty(false)

          // Hydrate content cache for both citations and embedded content
          const citationContentIds = docCitations.map((c) => c.content_id)
          const embeddedContentIds = docContent
            .map((section) => section.embedded_content_id)
            .filter((id): id is number => id !== null && id !== undefined)
          const allContentIds = [...new Set([...citationContentIds, ...embeddedContentIds])]
          void hydrateContentCache(allContentIds, setContentCache)
        }
      } catch (error) {
        console.error("Failed to load document", error)
        if (mounted) setStatus("error")
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [documentId])

  const wordCount = useMemo(() => sections.reduce((total, section) => total + countWords(section.content), 0), [sections])

  useEffect(() => {
    if (initialLoadRef.current) {
      initialLoadRef.current = false
      return
    }
    if (suppressDirtyRef.current) {
      suppressDirtyRef.current = false
      return
    }
    setDirty(true)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      void persistSections()
    }, 1000)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [sections])

  const persistSections = async () => {
    if (saveState === "saving") return
    if (!dirty) return
    setSaveState("saving")
    try {
      const saved = await saveDocumentContent(documentId, sectionsWithOrder(documentId, sections))
      suppressDirtyRef.current = true
      setSections(saved)
      setDirty(false)
      const updatedAt = latestUpdatedAt(saved) ?? new Date().toISOString()
      setLastSavedAt(updatedAt)
      setSaveState("idle")
    } catch (error) {
      console.error("Failed to save document", error)
      setSaveState("error")
      toast.error("Could not save document. We will keep your edits locally.")
    }
  }

  const handleSectionsChange = (contents: string[]) => {
    setSections((previous) => sectionsFromText(contents, documentId, previous))
  }

  const handleSelectionChange = (context: { text: string; start?: number; end?: number }) => {
    const start = context.start ?? 0
    const end = context.end ?? context.text.length
    const slice = start !== end ? context.text.slice(Math.min(start, end), Math.max(start, end)) : ""
    const next = (slice || context.text).trim()
    setSelectionText(next.slice(0, MAX_SELECTION_CONTEXT))
  }

  const handleCitationDrop = (sectionIndex: number, position: number, contentId: number) => {
    const marker = nextMarkerNumber(citations)
    const markerText = `[${marker}]`
    const absolutePosition = sectionAbsolutePosition(sections, sectionIndex, position)
    setSections((previous) => {
      const next = [...previous]
      const target = next[sectionIndex]
      if (!target) return previous
      const { updatedContent, updatedPosition } = mergeMarkerIntoExisting(target.content, position, markerText)
      next[sectionIndex] = { ...target, content: updatedContent }
      return next
    })

    setCitations((prev) => [...prev, { document_id: documentId, content_id: contentId, marker, position, section_index: sectionIndex }])
    void hydrateContentCache([contentId], setContentCache)

    void createCitation(documentId, {
      content_id: contentId,
      marker,
      position: absolutePosition,
      section_index: sectionIndex,
    }).catch((error) => {
      console.error("Failed to persist citation", error)
      toast.error("Could not save citation. The marker will stay locally.")
    })
  }

  const handleEmbeddedContentDrop = async (afterSectionIndex: number, contentId: number) => {
    const insertIndex = afterSectionIndex + 1
    const newSection: DocumentSection = {
      document_id: documentId,
      content: "",
      order_index: insertIndex,
      embedded_content_id: contentId,
    }

    // Update sections state
    let updatedSections: DocumentSection[] = []
    setSections((previous) => {
      const next = [...previous]
      next.splice(insertIndex, 0, newSection)
      updatedSections = next
      return next
    })

    // Hydrate the content cache
    void hydrateContentCache([contentId], setContentCache)

    // Immediately save the updated sections
    setSaveState("saving")
    try {
      const saved = await saveDocumentContent(documentId, sectionsWithOrder(documentId, updatedSections))
      suppressDirtyRef.current = true
      setSections(saved)
      setDirty(false)
      const updatedAt = latestUpdatedAt(saved) ?? new Date().toISOString()
      setLastSavedAt(updatedAt)
      setSaveState("idle")
    } catch (error) {
      console.error("Failed to save embedded content", error)
      setSaveState("error")
      toast.error("Could not save embedded content.")
    }
  }

  const handleCreateSection = (afterSectionIndex: number, options?: {
    initialContent?: string
  }) => {
    const insertIndex = afterSectionIndex + 1
    const newSection: DocumentSection = {
      document_id: documentId,
      content: options?.initialContent ?? "",
      order_index: insertIndex,
      embedded_content_id: null,
    }

    setSections((previous) => {
      const next = [...previous]
      next.splice(insertIndex, 0, newSection)
      return next
    })
  }

  const handleUpdateSectionContent = (sectionIndex: number, content: string) => {
    setSections((previous) => {
      const next = [...previous]
      const section = next[sectionIndex]
      if (!section) return previous

      // Never modify embedded content sections
      if (section.embedded_content_id) return previous

      next[sectionIndex] = {
        ...section,
        content,
        word_count: countWords(content),
      }
      return next
    })
  }

  const handleDeleteSection = (sectionIndex: number) => {
    // Prevent deleting the only section
    if (sections.length <= 1) {
      toast.error("Cannot delete the only section in the document.")
      return
    }

    const section = sections[sectionIndex]
    if (!section) return

    // Confirm deletion for non-empty text sections or embedded content
    const isEmpty = !section.embedded_content_id && section.content.trim() === ""
    const shouldConfirm = !isEmpty

    if (shouldConfirm) {
      const message = section.embedded_content_id
        ? "Delete this embedded content section?"
        : "Delete this section? This cannot be undone."

      // Simple browser confirm (we can enhance this later with a modal if needed)
      if (!window.confirm(message)) {
        return
      }
    }

    // Delete the section
    setSections((previous) => {
      const next = [...previous]
      next.splice(sectionIndex, 1)
      return next
    })

    // Focus management: move to section above or below
    // This will be handled by the editor's useEffect that checks selected index
  }

  const handleDuplicateSection = (sectionIndex: number) => {
    const section = sections[sectionIndex]
    if (!section) return

    const duplicatedSection: DocumentSection = {
      document_id: documentId,
      content: section.content,
      order_index: sectionIndex + 1,
      embedded_content_id: section.embedded_content_id,
      title: section.title,
    }

    setSections((previous) => {
      const next = [...previous]
      next.splice(sectionIndex + 1, 0, duplicatedSection)
      return next
    })

    toast.success("Section duplicated")
  }

  const handleReorderSection = (fromIndex: number, toIndex: number) => {
    setSections((previous) => {
      const next = [...previous]
      const [removed] = next.splice(fromIndex, 1)
      next.splice(toIndex, 0, removed)
      return next
    })
  }

  const handleTitleSave = async () => {
    if (!document) return
    const nextTitle = titleValue.trim()
    if (!nextTitle || nextTitle === document.title || titleSaving) return
    setTitleSaving(true)
    try {
      const updated = await updateDocumentTitle(document.id, nextTitle)
      setDocument(updated)
      setTitleValue(updated.title)
    } catch (error) {
      console.error("Failed to update title", error)
      toast.error("Could not update title. Please try again.")
      setTitleValue(document.title)
    } finally {
      setTitleSaving(false)
    }
  }

  const handleTitleKey = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter") {
      event.preventDefault()
      void handleTitleSave()
    }
  }

  // Keyboard shortcuts for toggling panels
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + B toggles left panel (Sources)
      if ((event.metaKey || event.ctrlKey) && event.key === 'b' && !event.shiftKey) {
        event.preventDefault()
        setShowSources((prev) => !prev)
        return
      }

      // Cmd/Ctrl + Shift + B toggles right panel (Assistant)
      if ((event.metaKey || event.ctrlKey) && event.key === 'B' && event.shiftKey) {
        event.preventDefault()
        setShowAssistant((prev) => !prev)
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  if (status === "loading") {
    return (
      <div className="h-full rounded-xl border bg-white p-6 shadow-sm">
        <div className="mb-4 h-6 w-1/3 animate-pulse rounded bg-muted" />
        <div className="grid h-[70vh] grid-cols-1 gap-4 lg:grid-cols-[320px_1fr_360px]">
          <div className="hidden h-full animate-pulse rounded-xl bg-muted lg:block" />
          <div className="h-full animate-pulse rounded-xl bg-muted" />
          <div className="hidden h-full animate-pulse rounded-xl bg-muted lg:block" />
        </div>
      </div>
    )
  }

  if (status === "error" || !document) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 rounded-xl border bg-white p-8 shadow-sm text-center">
        <p className="text-lg font-semibold">We couldn&apos;t load that document.</p>
        <p className="text-muted-foreground text-sm">Check the link or try refreshing.</p>
        <button
          onClick={() => router.push("/documents")}
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
        >
          Back to documents
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col bg-[#FEFEFE]">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/documents")}
            className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition hover:bg-slate-100 hover:text-foreground"
            aria-label="Back to documents"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <Input
              value={titleValue}
              onChange={(e) => setTitleValue(e.target.value)}
              onBlur={handleTitleSave}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault()
                  void handleTitleSave()
                }
              }}
              className="h-auto border-0 bg-transparent px-0 text-2xl font-semibold leading-tight shadow-none focus-visible:border-transparent focus-visible:ring-0"
              aria-label="Document title"
            />
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              {saveState === "saving" && <span>Saving…</span>}
              {saveState === "error" && <span className="text-destructive">Save failed</span>}
              {saveState === "idle" && !dirty && (
                <span className="flex items-center gap-1 text-emerald-600">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Saved
                </span>
              )}
              {dirty && saveState !== "saving" && <span className="text-amber-600">Pending save…</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSources((prev) => !prev)}
            className="flex h-9 w-9 items-center justify-center rounded-md transition hover:bg-slate-100"
            aria-label={showSources ? "Hide Sources (⌘B)" : "Show Sources (⌘B)"}
            title={showSources ? "Hide Sources (⌘B)" : "Show Sources (⌘B)"}
          >
            {showSources ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setShowAssistant((prev) => !prev)}
            className="flex h-9 w-9 items-center justify-center rounded-md transition hover:bg-slate-100"
            aria-label={showAssistant ? "Hide Assistant (⌘⇧B)" : "Show Assistant (⌘⇧B)"}
            title={showAssistant ? "Hide Assistant (⌘⇧B)" : "Show Assistant (⌘⇧B)"}
          >
            {showAssistant ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
          </button>
        </div>
      </header>

      <WorkspaceShell
        left={<SourcesPanel documentId={documentId} selectionText={selectionText} />}
        leftCollapsed={!showSources}
        leftWidth={leftWidth}
        onLeftResize={setLeftWidth}
        center={
          <div className="flex flex-col gap-4 pl-16 pr-6 py-8 pb-80">
          <DocumentEditor
            sections={sections}
            onSectionsChange={handleSectionsChange}
            onUpdateSectionContent={handleUpdateSectionContent}
            onSelectionChange={handleSelectionChange}
            onBlurSave={persistSections}
            onDropCitation={handleCitationDrop}
            onDropEmbeddedContent={handleEmbeddedContentDrop}
            onCreateSection={handleCreateSection}
            onDeleteSection={handleDeleteSection}
            onDuplicateSection={handleDuplicateSection}
            onReorderSection={handleReorderSection}
            contentCache={contentCache}
          />
        </div>
      }
      rightCollapsed={!showAssistant}
      rightWidth={rightWidth}
      onRightResize={setRightWidth}
        right={<AssistantPanel documentId={documentId} selectionText={selectionText} />}
      />
    </div>
  )
}

function countWords(text: string) {
  return text ? text.trim().split(/\s+/).filter(Boolean).length : 0
}

function sectionsFromText(contents: string[], documentId: number, previous: DocumentSection[]): DocumentSection[] {
  return contents.map((content, idx) => {
    const existing = previous[idx]
    return {
      id: existing?.id,
      document_id: documentId,
      content,
      order_index: idx,
      title: existing?.title ?? null,
      word_count: countWords(content),
      updated_at: existing?.updated_at,
      embedded_content_id: existing?.embedded_content_id ?? null,
    }
  })
}

function sectionsWithOrder(documentId: number, sections: DocumentSection[]): DocumentSection[] {
  return sections.map((section, idx) => ({
    ...section,
    document_id: documentId,
    order_index: idx,
  }))
}

function latestUpdatedAt(sections: DocumentSection[]): string | null {
  const timestamps = sections.map((section) => section.updated_at).filter(Boolean) as string[]
  if (!timestamps.length) return null
  return timestamps.sort().at(-1) ?? null
}

function nextMarkerNumber(citations: Citation[]) {
  const currentMax = citations.reduce((max, citation) => Math.max(max, citation.marker ?? 0), 0)
  return currentMax + 1
}

function sectionAbsolutePosition(sections: DocumentSection[], sectionIndex: number, position: number): number {
  const beforeLength = sections
    .slice(0, sectionIndex)
    .reduce((total, section) => total + section.content.length + 2, 0) // account for delimiter
  return beforeLength + position
}

function mergeMarkerIntoExisting(content: string, position: number, markerText: string) {
  const open = content.lastIndexOf("[", position)
  const close = content.indexOf("]", position)

  if (open !== -1 && close !== -1 && close > open) {
    const inside = content.slice(open + 1, close)
    // If inside is digits/commas, append marker instead of nesting
    if (/^\s*\d+(,\s*\d+)*\s*$/.test(inside)) {
      const prefix = content.slice(0, close)
      const suffix = content.slice(close)
      const updatedInside = inside.trim().length ? `${inside.trim()}, ${markerText.replace(/\[|\]/g, "")}` : markerText.replace(/\[|\]/g, "")
      return {
        updatedContent: `${content.slice(0, open + 1)}${updatedInside}${suffix}`,
        updatedPosition: close + markerText.length,
      }
    }
  }

  const before = content.slice(0, position)
  const after = content.slice(position)
  return {
    updatedContent: `${before}${markerText}${after}`,
    updatedPosition: position + markerText.length,
  }
}

async function hydrateContentCache(ids: number[], setCache?: React.Dispatch<React.SetStateAction<Record<number, ContentItem>>>) {
  if (!setCache) return
  const unique = Array.from(new Set(ids)).filter(Boolean)
  for (const id of unique) {
    try {
      const item = await fetchContentItem(id)
      setCache((prev) => (prev[id] ? prev : { ...prev, [id]: item }))
    } catch (error) {
      console.error("Failed to load content item", error)
    }
  }
}
