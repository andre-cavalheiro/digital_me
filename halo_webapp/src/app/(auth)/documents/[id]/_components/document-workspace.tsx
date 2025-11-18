"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { fetchDocument, fetchDocumentContent, type Document, type DocumentContent } from "@/lib/api"
import { WorkspaceShell } from "@/components/layout/workspace-shell"

type Props = {
  documentId: number
}

type FetchState = "idle" | "loading" | "error"

export function DocumentWorkspace({ documentId }: Props) {
  const router = useRouter()
  const [document, setDocument] = useState<Document | null>(null)
  const [content, setContent] = useState<DocumentContent | null>(null)
  const [status, setStatus] = useState<FetchState>("idle")

  useEffect(() => {
    let mounted = true
    const load = async () => {
      setStatus("loading")
      try {
        const [doc, docContent] = await Promise.all([fetchDocument(documentId), fetchDocumentContent(documentId)])
        if (mounted) {
          setDocument(doc)
          setContent(docContent)
          setStatus("idle")
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
    <div className="flex h-full flex-col gap-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{document.title}</h1>
          {(() => {
            const latestUpdatedAt = content?.reduce<string | undefined>((latest, section) => {
              if (section.updated_at && (!latest || new Date(section.updated_at) > new Date(latest))) {
                return section.updated_at
              }
              return latest
            }, undefined)
            return (
              <p className="text-muted-foreground text-sm">
                {latestUpdatedAt ? `Updated ${new Date(latestUpdatedAt).toLocaleString()}` : "Ready to start writing"}
              </p>
            )
          })()}
        </div>
      </header>

      <WorkspaceShell
        left={<PanelPlaceholder title="Sources" description="Drag sources into the document as citations." />}
        center={<DocumentAreaPlaceholder content={content ? content.map((s) => s.content).join("\n\n") : ""} />}
        right={<PanelPlaceholder title="Assistant" description="Start a conversation or attach context." />}
      />
    </div>
  )
}

function PanelPlaceholder({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-muted-foreground text-sm">{description}</p>
      <div className="flex-1 rounded-lg border border-dashed bg-muted/40" />
    </div>
  )
}

function DocumentAreaPlaceholder({ content }: { content: string }) {
  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <h2 className="text-lg font-semibold">Document</h2>
      <div className="flex-1 rounded-lg border bg-muted/10 p-4 text-muted-foreground">
        {content ? content : "Start typing to add your first paragraphs…"}
      </div>
    </div>
  )
}
