export default function LoadingDocument() {
  return (
    <div className="h-full rounded-xl border bg-white p-6 shadow-sm">
      <div className="mb-3 h-6 w-1/3 animate-pulse rounded bg-muted" />
      <div className="grid h-[70vh] grid-cols-1 gap-4 lg:grid-cols-[320px_1fr_360px]">
        <div className="hidden h-full animate-pulse rounded-xl bg-muted lg:block" />
        <div className="h-full animate-pulse rounded-xl bg-muted" />
        <div className="hidden h-full animate-pulse rounded-xl bg-muted lg:block" />
      </div>
    </div>
  )
}
