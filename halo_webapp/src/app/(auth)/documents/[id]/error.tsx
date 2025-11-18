"use client"

import { AlertTriangle } from "lucide-react"

export default function DocumentError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 rounded-xl border bg-white p-8 text-center shadow-sm">
      <AlertTriangle className="h-8 w-8 text-destructive" />
      <div>
        <p className="text-lg font-semibold">Unable to open document</p>
        <p className="text-muted-foreground text-sm">{error.message}</p>
      </div>
      <button
        onClick={() => reset()}
        className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
      >
        Try again
      </button>
    </div>
  )
}
