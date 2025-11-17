"use client"

import { useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { useAuth } from "@/lib/auth/context"
import { Button } from "@/components/ui/button"

export default function LandingPage() {
  const { userAuth, user, organization, signIn, loading } = useAuth()
  const router = useRouter()
  const isAuthenticated = Boolean(userAuth && user && organization)
  const isBootstrapping =
    loading || (userAuth && (!user || !organization))

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/home")
    }
  }, [isAuthenticated, router])

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <main className="relative z-10 flex flex-1 items-center justify-center px-6 py-20">
        <div className="flex max-w-3xl flex-col items-center gap-8 text-center">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight drop-shadow-sm sm:text-5xl md:text-6xl">
            <span className="block bg-gradient-to-r from-sky-300 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Welcome to:
            </span>
            <span className="mt-2 block text-slate-200">Halo Webapp</span>
          </h1>
          <p className="max-w-2xl text-base text-slate-300 sm:text-lg">
            By André Cavalheiro
          </p>
          <Button
            onClick={signIn}
            size="lg"
            className="cursor-pointer rounded-full bg-indigo-500/90 px-8 text-slate-50 shadow-xl shadow-indigo-900/40 transition-transform hover:-translate-y-0.5 hover:bg-indigo-400/90 focus-visible:ring-indigo-300"
          >
            Sign in with Google
          </Button>
        </div>
      </main>
    </div>
  )
}
