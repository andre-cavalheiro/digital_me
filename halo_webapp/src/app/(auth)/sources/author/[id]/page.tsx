"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft } from "lucide-react"
import { fetchAuthor, type AuthorWithContentCount } from "@/lib/api/authors"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AuthorDetailView } from "@/components/sources/author-detail-view"

export default function AuthorDetailPage() {
  const params = useParams()
  const router = useRouter()
  const authorId = params?.id ? parseInt(params.id as string, 10) : null

  const [author, setAuthor] = useState<AuthorWithContentCount | null>(null)
  const [status, setStatus] = useState<"idle" | "loading" | "error">("loading")
  const [errorMessage, setErrorMessage] = useState<string>("")

  useEffect(() => {
    if (!authorId || isNaN(authorId)) {
      setStatus("error")
      setErrorMessage("Invalid author ID")
      return
    }

    let mounted = true

    const loadAuthor = async () => {
      setStatus("loading")
      try {
        const data = await fetchAuthor(authorId)
        if (mounted) {
          setAuthor(data)
          setStatus("idle")
        }
      } catch (error) {
        console.error("Failed to load author", error)
        if (mounted) {
          setStatus("error")
          setErrorMessage("Failed to load author details. Please try again.")
        }
      }
    }

    loadAuthor()

    return () => {
      mounted = false
    }
  }, [authorId])

  if (status === "loading") {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    )
  }

  if (status === "error" || !author) {
    return (
      <div className="flex h-full flex-col gap-6 p-6">
        <Button
          variant="ghost"
          onClick={() => router.push("/sources")}
          className="w-fit"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Sources
        </Button>

        <Card className="border-destructive/20 bg-destructive/5 text-destructive">
          <CardHeader>
            <CardTitle>Unable to load author</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{errorMessage || "Author not found."}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return <AuthorDetailView author={author} />
}
