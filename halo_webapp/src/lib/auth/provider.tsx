"use client"

import { useRouter } from "next/navigation"
import { useContext, useEffect, useState } from "react"
import { isAxiosError } from "axios"
import {
  GoogleAuthProvider,
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  type User as UserAuth,
} from "firebase/auth"
import { fetchCurrentUser } from "@/lib/api/users"
import { fetchOrganization, createOrganization } from "@/lib/api/organizations"
import type { User, Organization } from "@/lib/api/types"
import { auth } from "./firebase"
import { AuthContext } from "./context"

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [userAuth, setUserAuth] = useState<UserAuth | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [organization, setOrganization] = useState<Organization | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (!firebaseUser) {
        setUserAuth(null)
        setUser(null)
        setOrganization(null)
        setLoading(false)
        return
      }

      setUserAuth(firebaseUser)

      try {
        let resolvedUser = await fetchCurrentUser()

        const provisionOrganization = async (): Promise<Organization> => {
          try {
            const createdOrganization = await createOrganization(
              firebaseUser.displayName?.trim() || "New Org",
            )
            resolvedUser = await fetchCurrentUser()
            return createdOrganization
          } catch (createError) {
            if (
              isAxiosError(createError) &&
              createError.response?.status === 409
            ) {
              // Organization already prepared in backend, just refresh local state
              resolvedUser = await fetchCurrentUser()
              return await fetchOrganization()
            }
            throw createError
          }
        }

        let resolvedOrganization: Organization

        if (!resolvedUser.id) {
          resolvedOrganization = await provisionOrganization()
        } else {
          try {
            resolvedOrganization = await fetchOrganization()
          } catch (organizationError) {
            if (
              isAxiosError(organizationError) &&
              [401, 403, 404].includes(
                organizationError.response?.status ?? 0,
              )
            ) {
              resolvedOrganization = await provisionOrganization()
            } else {
              throw organizationError
            }
          }
        }

        setUser(resolvedUser)
        setOrganization(resolvedOrganization)
      } catch (err) {
        console.error("❌ Bootstrap failed:", err)
      } finally {
        setLoading(false)
      }
    })

    return () => unsubscribe()
  }, [])

  const signIn = async () => {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
  }

  const signOut = async () => {
    await firebaseSignOut(auth)
    router.push("/") 
  }

  return (
    <AuthContext.Provider
      value={{
        userAuth,
        user,
        organization,
        loading,
        signIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
