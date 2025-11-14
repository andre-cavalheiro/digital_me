"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth/context"
import { Button } from "@/components/ui/button"

export default function LandingPage() {
  const { userAuth, signIn } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (userAuth) {
      router.push("/home")
    }
  }, [userAuth, router])

  return (
    <div className="h-screen flex flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold">Welcome to House Hunt</h1>
      <p className="text-muted-foreground text-sm">
        This will be your future landing page.
      </p>
      <Button onClick={signIn}>Sign in with Google</Button>
    </div>
  )
}
