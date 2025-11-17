import "@/app/globals.css"
import React from "react"
import { AuthProvider } from "@/lib/auth/provider"
import { ThemeProvider } from "@/components/theme-provider"

export const metadata = {
  title: "Digital Me",
  description: "AI-assisted writing with content from your curated sources",
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
