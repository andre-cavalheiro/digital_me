"use client"

import { useEffect, useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Toaster } from "sonner"
import { useAuth } from "@/lib/auth/context"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { PlayCircle, X } from "lucide-react"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { userAuth, user, organization, loading } = useAuth()
  const router = useRouter()
  const [showBanner, setShowBanner] = useState(false)
  const bannerStorageKey = "demoVideoBanner:dismissed"
  const [hasRedirected, setHasRedirected] = useState(false)

  useEffect(() => {
    // redirect immediately if not authenticated or org is missing
    if (!loading && !hasRedirected && (!userAuth || !user || !organization)) {
      setHasRedirected(true)
      router.replace("/") // force them back to landing page
    }
  }, [userAuth, user, organization, loading, router, hasRedirected])

  useEffect(() => {
    const dismissed = typeof window !== "undefined" ? window.localStorage.getItem(bannerStorageKey) : "false"
    setShowBanner(dismissed !== "true")
  }, [])

  const handleDismissBanner = () => {
    setShowBanner(false)
    if (typeof window !== "undefined") {
      window.localStorage.setItem(bannerStorageKey, "true")
    }
  }

  if (loading || !userAuth || !user || !organization) {
    return (
      <div className="flex items-center justify-center h-screen">
        <span className="text-muted-foreground">Loading your account...</span>
      </div>
    )
  }

  return (
    <>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
      <Toaster position="top-right" richColors closeButton />
    </>
  )
}
