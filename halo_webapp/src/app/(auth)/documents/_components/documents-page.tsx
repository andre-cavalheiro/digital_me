"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, RefreshCcw, Trash2 } from "lucide-react"
import { fetchDocuments, createDocument, deleteDocument, type Document } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"

type FetchState = "idle" | "loading" | "error"

export function DocumentsPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [status, setStatus] = useState<FetchState>("idle")
  const [creating, setCreating] = useState(false)

  const sortedDocuments = useMemo(
    () =>
      [...documents].sort((a, b) => {
        if (a.updated_at && b.updated_at) {
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        }
        return (b.id || 0) - (a.id || 0)
      }),
    [documents],
  )

  useEffect(() => {
    let mounted = true
    const load = async () => {
      setStatus("loading")
      try {
        const data = await fetchDocuments()
        if (mounted) {
          setDocuments(data)
          setStatus("idle")
        }
      } catch (error) {
        console.error("Failed to load documents", error)
        if (mounted) {
          setStatus("error")
        }
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  const handleCreate = async () => {
    setCreating(true)
    try {
      const doc = await createDocument({ title: undefined })
      setDocuments((prev) => [doc, ...prev])
      router.push(`/documents/${doc.id}`)
    } catch (error) {
      console.error("Failed to create document", error)
      setStatus("error")
    } finally {
      setCreating(false)
    }
  }

  const handleOpen = (id: number) => {
    router.push(`/documents/${id}`)
  }

  const handleDelete = async (id: number, title: string, event: React.MouseEvent) => {
    event.stopPropagation()

    if (!window.confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
      return
    }

    try {
      await deleteDocument(id)
      setDocuments((prev) => prev.filter((doc) => doc.id !== id))
      toast.success("Document deleted successfully")
    } catch (error) {
      console.error("Failed to delete document", error)
      toast.error("Failed to delete document. Please try again.")
    }
  }

  const isLoading = status === "loading" && documents.length === 0

  return (
    <div className="flex h-full flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Documents</h1>
          <p className="text-muted-foreground text-sm">Create, reopen, and jump back into your drafts.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => router.refresh()} disabled={status === "loading"}>
            <RefreshCcw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={handleCreate} disabled={creating}>
            <Plus className="mr-2 h-4 w-4" />
            {creating ? "Creating…" : "New Document"}
          </Button>
        </div>
      </div>

      {isLoading && <DocumentListSkeleton />}

      {status === "error" && !isLoading && (
        <Card className="border-destructive/20 bg-destructive/5 text-destructive">
          <CardHeader>
            <CardTitle>Unable to load documents</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Check your connection or try again.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && status !== "error" && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sortedDocuments.map((doc) => (
            <Card
              key={doc.id}
              className="group relative cursor-pointer transition hover:-translate-y-0.5 hover:shadow-md"
              onClick={() => handleOpen(doc.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="line-clamp-2 flex-1">{doc.title}</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-destructive hover:text-destructive-foreground"
                    onClick={(e) => handleDelete(doc.id, doc.title, e)}
                    aria-label={`Delete ${doc.title}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Updated {doc.updated_at ? new Date(doc.updated_at).toLocaleDateString() : "recently"}
                </p>
              </CardContent>
            </Card>
          ))}
          {sortedDocuments.length === 0 && status === "idle" && (
            <Card className="border-dashed text-muted-foreground">
              <CardHeader>
                <CardTitle>No documents yet</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">Click "New Document" to get started.</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

function DocumentListSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardHeader>
            <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
          </CardHeader>
          <CardContent>
            <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
