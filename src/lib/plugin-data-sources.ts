import type { PluginDataSourceId, PluginDataSource } from "./api/types"

export const PLUGIN_DATA_SOURCES: Record<PluginDataSourceId, PluginDataSource> = {
  cloudflare: {
    id: "cloudflare",
    displayName: "Cloudflare",
    icon: "/integrations/cloudflare.webp",
    enabled: true,
    getCapabilityBadges: () => [
      {
        label: "Managed Subdirectory Hosting",
        supported: true,
        tooltip: "Add /blog to your domain — hosted and routed automatically"
      }
    ]
  },
  namecheap: {
    id: "namecheap",
    displayName: "Namecheap",
    icon: "/integrations/namecheap.png",
    enabled: false,
    getCapabilityBadges: () => [
      {
        label: "Managed Subdirectory Hosting",
        supported: false,
        tooltip: "Add /blog to your domain — hosted and routed automatically"
      }
    ]
  }
}

