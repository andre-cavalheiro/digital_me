"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft } from "lucide-react"
import { fetchCollection, type CollectionWithContentCount } from "@/lib/api/collections"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CollectionDetailView } from "@/components/sources/collection-detail-view"

export default function CollectionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const collectionId = params?.id ? parseInt(params.id as string, 10) : null

  const [collection, setCollection] = useState<CollectionWithContentCount | null>(null)
  const [status, setStatus] = useState<"idle" | "loading" | "error">("loading")
  const [errorMessage, setErrorMessage] = useState<string>("")

  useEffect(() => {
    if (!collectionId || isNaN(collectionId)) {
      setStatus("error")
      setErrorMessage("Invalid collection ID")
      return
    }

    let mounted = true

    const loadCollection = async () => {
      setStatus("loading")
      try {
        const data = await fetchCollection(collectionId)
        if (mounted) {
          setCollection(data)
          setStatus("idle")
        }
      } catch (error) {
        console.error("Failed to load collection", error)
        if (mounted) {
          setStatus("error")
          setErrorMessage("Failed to load collection details. Please try again.")
        }
      }
    }

    loadCollection()

    return () => {
      mounted = false
    }
  }, [collectionId])

  if (status === "loading") {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    )
  }

  if (status === "error" || !collection) {
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
            <CardTitle>Unable to load collection</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{errorMessage || "Collection not found."}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return <CollectionDetailView collection={collection} />
}
