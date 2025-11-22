import type { PluginDataSourceId, PluginDataSource } from "./api/types"

export const PLUGIN_DATA_SOURCES: Record<PluginDataSourceId, PluginDataSource> = {
  x: {
    id: "x",
    displayName: "X",
    icon: "/integrations/x.png",
    enabled: true,
    getCapabilityBadges: () => [
      {
        label: "Tweet Access",
        supported: true,
        tooltip: "Access tweets via official X API - fresher data with rate limits"
      },
      {
        label: "Full Archive Search",
        supported: true,
        tooltip: "Search all tweets in X's full archive"
      }
    ]
  },
  community_archive: {
    id: "community_archive",
    displayName: "Community Archive",
    icon: "/integrations/community_archive.avif",
    enabled: true,
    getCapabilityBadges: () => [
      {
        label: "Tweet Access",
        supported: true,
        tooltip: "Access tweets via community-managed archive - open source"
      },
      {
        label: "Historical Data",
        supported: true,
        tooltip: "Access to community-archived historical tweet data"
      }
    ]
  }
}

