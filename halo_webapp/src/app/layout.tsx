import "@/app/globals.css"
import React from "react"
import { AuthProvider } from "@/lib/auth/provider"
import { ThemeProvider } from "@/components/theme-provider"

export const metadata = {
  title: "Halo Webapp",
  description: "A general purpose NextJS webapp",
  icons: {
    icon: "/favicon.ico",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
