type WorkspaceShellProps = {
  left?: React.ReactNode
  center: React.ReactNode
  right?: React.ReactNode
  leftCollapsed?: boolean
  rightCollapsed?: boolean
  leftWidth?: number
  rightWidth?: number
  onLeftResize?: (width: number) => void
  onRightResize?: (width: number) => void
}

/**
 * Three-column shell to mimic the wireframe: sources (left), document (center), assistant (right).
 * Keeps gutters consistent and lets panels scroll independently.
 */
export function WorkspaceShell({
  left,
  center,
  right,
  leftCollapsed,
  rightCollapsed,
  leftWidth = 320,
  rightWidth = 360,
  onLeftResize,
  onRightResize,
}: WorkspaceShellProps) {
  const showLeft = Boolean(left && !leftCollapsed)
  const showRight = Boolean(right && !rightCollapsed)

  const startResize = (side: "left" | "right", event: React.MouseEvent<HTMLDivElement>) => {
    event.preventDefault()
    const startX = event.clientX
    const startWidth = side === "left" ? leftWidth : rightWidth
    const clamp = (value: number) => Math.min(520, Math.max(240, value))

    const handleMove = (moveEvent: MouseEvent) => {
      const delta = moveEvent.clientX - startX
      if (side === "left" && onLeftResize) {
        onLeftResize(clamp(startWidth + delta))
      }
      if (side === "right" && onRightResize) {
        onRightResize(clamp(startWidth - delta))
      }
    }

    const handleUp = () => {
      window.removeEventListener("mousemove", handleMove)
      window.removeEventListener("mouseup", handleUp)
    }

    window.addEventListener("mousemove", handleMove)
    window.addEventListener("mouseup", handleUp)
  }

  return (
    <div className="flex h-full overflow-hidden bg-[#FEFEFE]">
      {showLeft && (
        <section style={{ width: leftWidth }} className="hidden min-w-[240px] max-w-[520px] flex-col overflow-hidden border-r bg-slate-50 lg:flex">
          {left}
        </section>
      )}
      {showLeft && onLeftResize && <div className="hidden w-1 cursor-col-resize bg-gradient-to-r from-transparent via-slate-300 to-transparent lg:block" onMouseDown={(e) => startResize("left", e)} />}

      <section className="flex min-w-[0] flex-1 flex-col overflow-y-auto bg-[#FEFEFE]">{center}</section>

      {showRight && onRightResize && <div className="hidden w-1 cursor-col-resize bg-gradient-to-r from-transparent via-slate-300 to-transparent lg:block" onMouseDown={(e) => startResize("right", e)} />}
      {showRight && (
        <section style={{ width: rightWidth }} className="hidden min-w-[240px] max-w-[520px] flex-col overflow-hidden border-l bg-slate-50 lg:flex">
          {right}
        </section>
      )}
    </div>
  )
}
