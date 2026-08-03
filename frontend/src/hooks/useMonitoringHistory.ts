import { useQuery } from "@tanstack/react-query";
import { getMonitoringHistory } from "../services/dashboard";

export interface MonitoringHistory {
  id: number;
  asset_id: number;
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  network_sent: number;
  network_received: number;
  created_at: string;
}

export type MonitoringRange = "1h" | "24h" | "7d";

export const useMonitoringHistory = (
  assetId: number,
  range?: MonitoringRange
) => {
  return useQuery<MonitoringHistory[]>({
    queryKey: ["monitoring-history", assetId, range ?? "all"],
    queryFn: () => getMonitoringHistory(assetId, range),
    // Feature 1 requirement: graphs auto-refresh every 5 seconds.
    refetchInterval: 5000,
    enabled: Number.isFinite(assetId) && assetId > 0,
  });
};
