"use client"

import type { ReactNode } from "react"

type Metric = {
  label: string
  value: number
  icon?: ReactNode
}

type MetricsDisplayProps = {
  metrics: Metric[]
  size?: "sm" | "md"
}

/**
  * Generic metrics renderer that hides zero values.
  */
export function MetricsDisplay({ metrics, size = "sm" }: MetricsDisplayProps) {
  const textClass = size === "sm" ? "text-xs" : "text-sm"
  const visibleMetrics = metrics.filter((metric) => metric.value > 0)

  if (visibleMetrics.length === 0) return null

  return (
    <div className={`flex gap-4 ${textClass} text-slate-500`}>
      {visibleMetrics.map((metric) => (
        <span key={metric.label} className="flex items-center gap-1">
          {metric.icon}
          {metric.value.toLocaleString()} {metric.label}
        </span>
      ))}
    </div>
  )
}

export type { Metric, MetricsDisplayProps }
