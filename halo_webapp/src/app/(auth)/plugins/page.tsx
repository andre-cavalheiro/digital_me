'use client'

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip"
import { Trash2, Settings, CheckCircle, XCircle } from "lucide-react"
import { fetchPlugins as getPlugins, createPlugin, deletePlugin } from "@/lib/api/plugins"
import type { Plugin, PluginCreate, PluginDataSourceId } from "@/lib/api/types"
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import { PageHeader } from "@/components/ui/page-header"
import { PLUGIN_DATA_SOURCES } from "@/lib/plugin-data-sources"
import { startXOauth } from "@/lib/integrations/x/oauth"

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([])
  const [loading, setLoading] = useState(true)
  const [installingPlugin, setInstallingPlugin] = useState<string | null>(null)
  const [deletingPlugin, setDeletingPlugin] = useState<PluginDataSourceId | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<PluginDataSourceId | null>(null)
  const [installDialogOpen, setInstallDialogOpen] = useState<PluginDataSourceId | null>(null)

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const pluginsData = await getPlugins()
        setPlugins(pluginsData)
      } catch (error) {
        console.error("Error fetching plugins:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchPlugins()
  }, [])

  const handleInstall = async (platformId: string, platformDisplayName: string) => {
    setInstallingPlugin(platformId)
    try {
      const existing = getPluginForPlatform(platformId)
      const plugin = existing
        ? existing
        : await createPlugin({
            title: platformDisplayName,
            data_source: platformId as any,
            credentials: { status: "pending" },
            properties: {},
          })

      if (!existing) {
        setPlugins(prev => [...prev, plugin])
      }

      if (platformId === "x") {
        setInstallDialogOpen(null)
        await startXOauth(plugin.id, "/plugins", !existing)
        return
      }

      toast.success(`${platformDisplayName} integration installed successfully`)
      setInstallDialogOpen(null)
    } catch (error) {
      console.error("Error installing plugin:", error)
      toast.error(`Failed to install ${platformDisplayName} integration`)
    } finally {
      setInstallingPlugin(null)
    }
  }

  const handleDelete = async (pluginDataSource: PluginDataSourceId) => {
    const plugin = getPluginForPlatform(pluginDataSource)
    if (!plugin) {
      toast.error("Integration not found")
      return
    }

    setDeletingPlugin(pluginDataSource)
    try {
      await deletePlugin(plugin.id)
      setPlugins(prev => prev.filter(p => p.dataSource !== plugin.dataSource))
      toast.success("Integration deleted successfully")
    } catch (error) {
      console.error("Error deleting plugin:", error)
      toast.error("Failed to delete integration")
    } finally {
      setDeletingPlugin(null)
    }
  }

  const getPluginForPlatform = (platform: string) => {
    if (!Array.isArray(plugins)) {
      console.warn("Plugins is not an array:", plugins)
      return undefined
    }
    return plugins.find(p => p.dataSource === platform)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <span className="text-muted-foreground">Loading integrations...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background p-4">
        {/* Header */}
        <PageHeader
          title="Automations"
          description="Configure what should happen when new houses hit the market"
          centered={false}
        />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        {/* Platforms Section */}
        <div className="mb-8">
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-2">Platform Integrations</h2>
            <p className="text-muted-foreground">Connect your accounts to enable quick or automatic applications to houses</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
            {Object.values(PLUGIN_DATA_SOURCES).map((platform) => {
              const plugin = getPluginForPlatform(platform.id);
              const isInstalled = !!plugin;
              const canInstall = platform.enabled;
              const badges = platform.getCapabilityBadges();

              return (
                <Card key={platform.id} className={cn(
                  "group relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5",
                  !canInstall && "opacity-75"
                )}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-muted/50 to-muted flex items-center justify-center shadow-sm flex-shrink-0">
                          <img
                            src={platform.icon}
                            alt={platform.displayName}
                            className="w-6 h-6 object-contain"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                              e.currentTarget.nextElementSibling?.classList.remove('hidden');
                            }}
                          />
                          <Settings className="w-6 h-6 hidden text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-3">
                            <CardTitle className="text-base font-semibold truncate">{platform.displayName}</CardTitle>
                          </div>
                        </div>
                      </div>

                      {/* Delete button positioned at top right */}
                      {isInstalled && (
                        <Dialog
                          open={deleteDialogOpen === platform.id}
                          onOpenChange={(open) => setDeleteDialogOpen(open ? platform.id : null)}
                        >
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors flex-shrink-0 cursor-pointer"
                              disabled={deletingPlugin === platform.id}
                              data-gtm-event="integration_delete"
                              data-gtm-name={`Integration – Delete ${platform.displayName}`}
                              data-gtm-id={`integration_delete_${platform.id}`}
                              data-gtm-context="automations"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Delete Integration</DialogTitle>
                            </DialogHeader>
                            <div className="py-4">
                              <p className="text-sm text-muted-foreground">
                                Are you sure you want to delete the {platform.displayName} integration? This action cannot be undone.
                              </p>
                            </div>
                            <div className="flex justify-end gap-2">
                              <Button
                                type="button"
                                variant="outline"
                                className="cursor-pointer"
                                onClick={() => setDeleteDialogOpen(null)}
                                data-gtm-event="dialog_action"
                                data-gtm-name="Integration Delete – Cancel"
                                data-gtm-id="integration_delete_cancel"
                                data-gtm-context="automations"
                              >
                                Cancel
                              </Button>
                              <Button
                                type="button"
                                variant="destructive"
                                className="cursor-pointer"
                                onClick={() => {
                                  handleDelete(platform.id)
                                  setDeleteDialogOpen(null)
                                }}
                                disabled={deletingPlugin === platform.id}
                                data-gtm-event="dialog_action"
                                data-gtm-name={`Integration Delete – Confirm ${platform.displayName}`}
                                data-gtm-id={`integration_delete_confirm_${platform.id}`}
                                data-gtm-context="automations"
                              >
                                {deletingPlugin === platform.id ? "Deleting..." : "Delete"}
                              </Button>
                            </div>
                          </DialogContent>
                        </Dialog>
                      )}
                    </div>

                    {/* Feature lines moved to separate section with proper spacing */}
                    <div className="ml-13 space-y-1.5">
                      {badges.map((badge, idx) => (
                        <Tooltip key={idx}>
                          <TooltipTrigger asChild>
                            <div className="flex items-center gap-2 text-sm">
                              <span className="text-muted-foreground">
                                {badge.label}
                              </span>
                              {badge.supported ? (
                                <CheckCircle className="w-4 h-4 flex-shrink-0" style={{ color: '#86efac' }} />
                              ) : (
                                <XCircle className="w-4 h-4 flex-shrink-0" style={{ color: '#fda4af' }} />
                              )}
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="max-w-xs">
                              {badge.tooltip}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </div>
                  </CardHeader>

                  <CardContent className="pt-0">
                    {isInstalled ? (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            className="w-full cursor-default bg-emerald-500 text-white border-emerald-500 hover:bg-emerald-500 font-medium"
                          >
                            Active
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-xs">
                            Your {platform.displayName} account is connected. You can apply to houses from {platform.displayName} directly from HomeSeek.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    ) : canInstall ? (
                      <Dialog
                        open={installDialogOpen === platform.id}
                        onOpenChange={open => setInstallDialogOpen(open ? platform.id : null)}
                      >
                        <DialogTrigger asChild>
                          <Button
                            className="w-full cursor-pointer bg-primary hover:bg-primary/90 transition-colors"
                            disabled={installingPlugin === platform.id}
                            data-gtm-event="integration_install"
                            data-gtm-name={`Integration – Install ${platform.displayName}`}
                            data-gtm-id={`integration_install_${platform.id}`}
                            data-gtm-context="automations"
                          >
                            {installingPlugin === platform.id ? "Installing..." : "Install"}
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Install {platform.displayName} Integration</DialogTitle>
                          </DialogHeader>
                          <div className="py-4">
                            <p className="text-sm text-muted-foreground">
                              Click Install to enable the {platform.displayName} integration. This will allow you to access tweets and content from {platform.displayName}.
                            </p>
                          </div>
                          <div className="flex justify-end gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              className="cursor-pointer"
                              onClick={() => setInstallDialogOpen(null)}
                              data-gtm-event="dialog_action"
                              data-gtm-name="Integration Install – Cancel"
                              data-gtm-id="integration_install_cancel"
                              data-gtm-context="automations"
                            >
                              Cancel
                            </Button>
                            <Button
                              type="button"
                              className="cursor-pointer"
                              onClick={() => handleInstall(platform.id, platform.displayName)}
                              disabled={installingPlugin === platform.id}
                              data-gtm-event="dialog_action"
                              data-gtm-name={`Integration Install – Confirm ${platform.displayName}`}
                              data-gtm-id={`integration_install_confirm_${platform.id}`}
                              data-gtm-context="automations"
                            >
                              {installingPlugin === platform.id ? "Installing..." : "Install"}
                            </Button>
                          </div>
                        </DialogContent>
                      </Dialog>
                    ) : (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            className="w-full cursor-not-allowed bg-muted text-muted-foreground border-muted hover:bg-muted"
                            disabled
                          >
                            Install
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-xs">
                            Connection with your platform account is not yet allowed as "Easy Apply" is not yet supported for this platform
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
    </TooltipProvider>
  )
}
