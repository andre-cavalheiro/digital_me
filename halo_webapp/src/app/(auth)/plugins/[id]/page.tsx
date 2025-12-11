"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, BookMarked, Folder, RefreshCw, Twitter, Play, AlertCircle } from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/ui/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { fetchPlugins } from "@/lib/api/plugins"
import { fetchCollections } from "@/lib/api/collections"
import { triggerPluginJob } from "@/lib/api/plugins"
import type { Plugin } from "@/lib/api/types"
import type { Collection } from "@/lib/api/schemas/collection"

export default function PluginDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = Number(params.id)

  const [plugin, setPlugin] = useState<Plugin | null>(null)
  const [loading, setLoading] = useState(true)
  const [collections, setCollections] = useState<Collection[]>([])
  const [loadingCollections, setLoadingCollections] = useState(false)
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        const plugins = await fetchPlugins()
        const found = plugins.find(p => p.id === id)

        if (!found) {
          toast.error("Plugin not found")
          router.push("/plugins")
          return
        }

        setPlugin(found)

        // If X plugin, load collections immediately
        if (found.dataSource === "x") {
          await loadCollections(found.id)
        }
      } catch (error) {
        console.error("Error loading plugin:", error)
        toast.error("Failed to load plugin details")
      } finally {
        setLoading(false)
      }
    }

    if (!isNaN(id)) {
      loadData()
    }
  }, [id, router])

  const loadCollections = async (pluginId: number) => {
    setLoadingCollections(true)
    try {
      const data = await fetchCollections({
        pluginId: pluginId,
        type: "bookmark_folder",
        limit: 100, // Fetch up to 100 folders
      })
      setCollections(data)
    } catch (error) {
      console.error("Error loading collections:", error)
      toast.error("Failed to load bookmark folders")
    } finally {
      setLoadingCollections(false)
    }
  }

  const handleTriggerJob = async (jobType: string, jobParams: Record<string, any> = {}, label: string) => {
    if (!plugin) return

    setTriggeringJob(jobType + (jobParams.collection_id ? `-${jobParams.collection_id}` : ""))
    try {
      await triggerPluginJob(plugin.id, jobType, jobParams)
      toast.success(`Job "${label}" started successfully`)

      // Reload collections if we just synced folders
      if (jobType === "sync_folders") {
        // Wait a moment for async job to potentially finish (or just refresh immediately to show loading state if we had one)
        // For now just trigger a reload after a short delay
        setTimeout(() => loadCollections(plugin.id), 2000)
      }
    } catch (error) {
      console.error(`Error triggering ${jobType}:`, error)
      toast.error(`Failed to start job "${label}"`)
    } finally {
      setTriggeringJob(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-4 flex items-center justify-center">
        <div className="text-muted-foreground">Loading plugin details...</div>
      </div>
    )
  }

  if (!plugin) return null

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-5xl mx-auto">
        <Button
          variant="ghost"
          className="mb-4 pl-0 hover:pl-0 hover:bg-transparent text-muted-foreground hover:text-foreground transition-colors"
          onClick={() => router.push("/plugins")}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Plugins
        </Button>

        <PageHeader
          title={plugin.title}
          description={`Manage your ${plugin.dataSource} integration settings and data sync.`}
          centered={false}
        />

        {plugin.dataSource === "x" ? (
          <div className="space-y-8 mt-8">
            {/* Global Sync Actions */}
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookMarked className="w-5 h-5 text-primary" />
                    All Bookmarks
                  </CardTitle>
                  <CardDescription>
                    Sync all your X bookmarks into the "My X Bookmarks" collection.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    className="w-full"
                    onClick={() => handleTriggerJob("fetch_all_bookmarks", {}, "Fetch All Bookmarks")}
                    disabled={!!triggeringJob}
                  >
                    {triggeringJob === "fetch_all_bookmarks" ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4 mr-2" />
                    )}
                    Sync All Bookmarks
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Folder className="w-5 h-5 text-primary" />
                    Bookmark Folders
                  </CardTitle>
                  <CardDescription>
                    Sync your bookmark folders list from X.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={() => handleTriggerJob("sync_folders", {}, "Sync Folders List")}
                    disabled={!!triggeringJob}
                  >
                    {triggeringJob === "sync_folders" ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4 mr-2" />
                    )}
                    Refresh Folders List
                  </Button>
                </CardContent>
              </Card>
            </div>

            <Separator />

            {/* Folders List */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold tracking-tight">Available Folders</h2>
                <Badge variant="outline" className="ml-2">
                  {collections.length} folders
                </Badge>
              </div>

              {loadingCollections ? (
                <div className="text-center py-12 text-muted-foreground">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading folders...
                </div>
              ) : collections.length === 0 ? (
                <Card className="bg-muted/50 border-dashed">
                  <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                    <AlertCircle className="w-10 h-10 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">No folders found</h3>
                    <p className="text-muted-foreground max-w-sm mt-2 mb-6">
                      Sync your folders list to see available bookmark folders here.
                    </p>
                    <Button
                      variant="secondary"
                      onClick={() => handleTriggerJob("sync_folders", {}, "Sync Folders List")}
                      disabled={!!triggeringJob}
                    >
                      Sync Folders List
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {collections.map((collection) => (
                    <Card key={collection.id} className="overflow-hidden">
                      <CardHeader className="p-4 pb-2">
                        <CardTitle className="text-base truncate" title={collection.name}>
                          {collection.name}
                        </CardTitle>
                        <CardDescription className="text-xs truncate">
                          ID: {collection.external_id}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="p-4 pt-2">
                        <div className="flex items-center justify-between mt-2">
                          <div className="text-xs text-muted-foreground">
                            {collection.last_synced_at ? (
                              `Synced ${new Date(collection.last_synced_at).toLocaleDateString()}`
                            ) : (
                              "Never synced"
                            )}
                          </div>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleTriggerJob(
                              "fetch_folder_content",
                              { collection_id: collection.id },
                              `Sync ${collection.name}`
                            )}
                            disabled={!!triggeringJob}
                          >
                            {triggeringJob === `fetch_folder_content-${collection.id}` ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                            <span className="ml-2">Sync</span>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-muted-foreground">
            Configuration UI for {plugin.dataSource} is not yet implemented.
          </div>
        )}
      </div>
    </div>
  )
}
