"use client"

import { useEffect, useMemo, useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { Loader2, User } from "lucide-react"
import {
  fetchCollectionAuthorStatistics,
  type AuthorContribution,
  type CollectionAuthorStatistics,
} from "@/lib/api/collections"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type CollectionAuthorPieChartProps = {
  collectionId: number
}

type NormalizedContributor = AuthorContribution & { key: string }

const formatHandle = (handle?: string | null) => {
  if (!handle) return ""
  return handle.startsWith("@") ? handle : `@${handle}`
}

const ContributorRow = ({ contributor, rank }: { contributor: NormalizedContributor; rank: number }) => {
  const handle = formatHandle(contributor.handle)
  const accent =
    rank === 1
      ? "border-amber-200 bg-amber-50"
      : rank <= 3
        ? "border-blue-100 bg-blue-50"
        : "border-slate-100 bg-white"

  const content = (
    <div
      className={`flex items-center gap-3 rounded-xl border px-3 py-2 transition hover:-translate-y-0.5 hover:shadow-sm ${accent}`}
    >
      <div className="w-10 text-center text-sm font-semibold text-slate-400">#{rank}</div>
      <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-full bg-slate-100">
        {contributor.avatarUrl ? (
          <Image
            src={contributor.avatarUrl}
            alt={contributor.displayName}
            fill
            className="object-cover"
            sizes="48px"
            unoptimized
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <User className="h-5 w-5 text-slate-400" />
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-900">{contributor.displayName}</p>
        <p className="truncate text-xs text-slate-500">{handle}</p>
      </div>
      <div className="text-right text-sm font-semibold text-slate-900">{contributor.contentCount}</div>
      <div className="w-16 text-right text-xs font-medium text-slate-600">
        {contributor.percentage.toFixed(1)}%
      </div>
    </div>
  )

  if (contributor.authorId) {
    return (
      <Link href={`/sources/author/${contributor.authorId}`} className="block">
        {content}
      </Link>
    )
  }

  return content
}

export function CollectionAuthorPieChart({ collectionId }: CollectionAuthorPieChartProps) {
  const [statistics, setStatistics] = useState<CollectionAuthorStatistics | null>(null)
  const [status, setStatus] = useState<"idle" | "loading" | "error">("loading")
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    let mounted = true
    setExpanded(false)

    const loadStatistics = async () => {
      setStatus("loading")
      try {
        const data = await fetchCollectionAuthorStatistics(collectionId)
        if (mounted) {
          setStatistics(data)
          setStatus("idle")
        }
      } catch (error) {
        console.error("Failed to load author statistics", error)
        if (mounted) {
          setStatus("error")
        }
      }
    }

    loadStatistics()

    return () => {
      mounted = false
    }
  }, [collectionId])

  const contributors: NormalizedContributor[] = useMemo(() => {
    if (!statistics) return []
    return statistics.contributors.map((contributor, index) => ({
      ...contributor,
      key: contributor.authorId ? String(contributor.authorId) : `${contributor.handle || "c"}-${index}`,
    }))
  }, [statistics])

  const sortedContributors = useMemo(
    () => [...contributors].sort((a, b) => b.contentCount - a.contentCount),
    [contributors],
  )
  const visibleContributors = expanded ? sortedContributors : sortedContributors.slice(0, 5)

  if (status === "loading") {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
        </CardContent>
      </Card>
    )
  }

  if (status === "error" || !statistics) {
    return (
      <Card className="border-destructive/20 bg-destructive/5">
        <CardContent className="py-6 text-center text-sm text-destructive">
          Failed to load author statistics
        </CardContent>
      </Card>
    )
  }

  if (sortedContributors.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-8 text-center text-sm text-slate-500">
          No author data available for this collection
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center justify-between">
          <span>Contributor Ranking</span>
          <span className="text-sm font-normal text-slate-500">
            {statistics.uniqueAuthorCount} {statistics.uniqueAuthorCount === 1 ? "author" : "authors"}
          </span>
        </CardTitle>
        <p className="text-sm text-slate-500">Top contributors by items saved into this collection.</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
          <span>
            <span className="font-semibold text-slate-900">{statistics.totalContentCount}</span> items saved
          </span>
          <span>
            <span className="font-semibold text-slate-900">{sortedContributors.length}</span> contributors listed
          </span>
        </div>

        <div className="space-y-3">
          {visibleContributors.map((contributor, index) => (
            <ContributorRow
              key={contributor.key}
              contributor={contributor}
              rank={index + 1}
            />
          ))}
        </div>

        {sortedContributors.length > 5 && (
          <div className="flex items-center justify-between pt-2">
            <p className="text-sm text-slate-500">
              Showing {visibleContributors.length} of {sortedContributors.length} contributors
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpanded((prev) => !prev)}
            >
              {expanded ? "Collapse to top 5" : `Show all (${sortedContributors.length})`}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
