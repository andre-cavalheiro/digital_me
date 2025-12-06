"use client"

import type { ReactNode } from "react"
import Image from "next/image"
import type { Author } from "@/lib/api"
import { Badge } from "@/components/ui/badge"

type AuthorBadgeProps = {
  author: Author
  size?: "sm" | "md" | "lg"
  showPlatform?: boolean
  showBio?: boolean
  children?: ReactNode
}

/**
  * Platform-agnostic author display from the author table.
  * Provides optional slots for platform-specific embellishments.
  */
export function AuthorBadge({
  author,
  size = "md",
  showPlatform = false,
  showBio = false,
  children,
}: AuthorBadgeProps) {
  const avatarSize = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
  }[size]

  const textSize = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  }[size]

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0">
        <div className={`relative ${avatarSize} overflow-hidden rounded-full bg-slate-200`}>
          <Image
            src={author.avatar_url}
            alt={author.display_name}
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1">
          <span className={`truncate font-semibold ${textSize} text-slate-900`}>
            {author.display_name}
          </span>

          {showPlatform && (
            <Badge variant="outline" className="text-xs">
              {author.platform}
            </Badge>
          )}

          <span className={`truncate ${textSize} text-slate-500`}>@{author.handle}</span>

          {children}
        </div>

        {showBio && author.bio && (
          <p className="mt-0.5 line-clamp-2 text-xs text-slate-600">
            {author.bio}
          </p>
        )}
      </div>
    </div>
  )
}
