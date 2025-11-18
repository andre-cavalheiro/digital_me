export default function LoadingDocuments() {
  return (
    <div className="h-full animate-pulse rounded-xl border bg-white p-6 shadow-sm">
      <div className="mb-4 h-6 w-1/3 rounded bg-muted" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="rounded-xl border bg-white p-6 shadow-sm">
            <div className="mb-4 h-5 w-2/3 rounded bg-muted" />
            <div className="h-4 w-1/2 rounded bg-muted" />
          </div>
        ))}
      </div>
    </div>
  )
}
