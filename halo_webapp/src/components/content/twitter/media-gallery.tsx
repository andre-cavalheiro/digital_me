"use client"

import Image from "next/image"
import type { TwitterMedia } from "@/lib/api"

export type MediaGalleryProps = {
  media: TwitterMedia[]
  compact?: boolean
}

/**
 * Displays tweet media (photos/videos) in a responsive grid layout
 * - Single image: Full width
 * - Two images: Side by side
 * - Three images: First image full width, two on bottom
 * - Four images: 2x2 grid
 */
export function MediaGallery({ media, compact = false }: MediaGalleryProps) {
  // Filter to only show photos for now (videos/GIFs can be added later)
  const photos = media.filter(m => m.type === 'photo' && m.url)

  if (photos.length === 0) return null

  const heightClass = compact ? "max-h-48" : "max-h-96"

  // Single image - full width
  if (photos.length === 1) {
    const photo = photos[0]
    return (
      <div className={`mt-2 overflow-hidden rounded-lg border border-slate-200 ${heightClass}`}>
        <Image
          src={photo.url!}
          alt={photo.alt_text || "Tweet image"}
          width={photo.width || 600}
          height={photo.height || 400}
          className="h-full w-full object-cover"
          unoptimized
        />
      </div>
    )
  }

  // Two images - side by side
  if (photos.length === 2) {
    return (
      <div className={`mt-2 grid grid-cols-2 gap-1 ${heightClass}`}>
        {photos.map((photo, index) => (
          <div key={photo.media_key} className="overflow-hidden rounded-lg border border-slate-200">
            <Image
              src={photo.url!}
              alt={photo.alt_text || `Tweet image ${index + 1}`}
              width={photo.width || 400}
              height={photo.height || 400}
              className="h-full w-full object-cover"
              unoptimized
            />
          </div>
        ))}
      </div>
    )
  }

  // Three images - first full width, two on bottom
  if (photos.length === 3) {
    return (
      <div className={`mt-2 grid grid-rows-2 gap-1 ${heightClass}`}>
        <div className="overflow-hidden rounded-lg border border-slate-200">
          <Image
            src={photos[0].url!}
            alt={photos[0].alt_text || "Tweet image 1"}
            width={photos[0].width || 600}
            height={photos[0].height || 300}
            className="h-full w-full object-cover"
            unoptimized
          />
        </div>
        <div className="grid grid-cols-2 gap-1">
          {photos.slice(1).map((photo, index) => (
            <div key={photo.media_key} className="overflow-hidden rounded-lg border border-slate-200">
              <Image
                src={photo.url!}
                alt={photo.alt_text || `Tweet image ${index + 2}`}
                width={photo.width || 300}
                height={photo.height || 200}
                className="h-full w-full object-cover"
                unoptimized
              />
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Four images - 2x2 grid
  return (
    <div className={`mt-2 grid grid-cols-2 grid-rows-2 gap-1 ${heightClass}`}>
      {photos.slice(0, 4).map((photo, index) => (
        <div key={photo.media_key} className="overflow-hidden rounded-lg border border-slate-200">
          <Image
            src={photo.url!}
            alt={photo.alt_text || `Tweet image ${index + 1}`}
            width={photo.width || 300}
            height={photo.height || 300}
            className="h-full w-full object-cover"
            unoptimized
          />
        </div>
      ))}
    </div>
  )
}
