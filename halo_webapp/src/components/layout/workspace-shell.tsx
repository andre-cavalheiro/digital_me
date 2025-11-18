type WorkspaceShellProps = {
  left?: React.ReactNode
  center: React.ReactNode
  right?: React.ReactNode
}

/**
 * Three-column shell to mimic the wireframe: sources (left), document (center), assistant (right).
 * Keeps gutters consistent and lets panels scroll independently.
 */
export function WorkspaceShell({ left, center, right }: WorkspaceShellProps) {
  return (
    <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-[320px_1fr_360px]">
      {left && <section className="hidden lg:flex flex-col overflow-hidden rounded-xl border bg-white shadow-sm">{left}</section>}
      <section className="flex flex-col overflow-hidden rounded-xl border bg-white shadow-sm">{center}</section>
      {right && <section className="hidden lg:flex flex-col overflow-hidden rounded-xl border bg-white shadow-sm">{right}</section>}
    </div>
  )
}
