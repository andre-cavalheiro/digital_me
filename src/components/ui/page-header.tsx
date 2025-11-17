import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: string
  description?: string
  centered?: boolean
  className?: string
}

export function PageHeader({
  title,
  description,
  centered = true,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "mb-8",
        centered && "text-center",
        className
      )}
    >
      <h1 className="text-3xl font-bold tracking-tight mb-2">{title}</h1>
      {description && (
        <p className="text-muted-foreground text-lg">{description}</p>
      )}
    </div>
  )
}
