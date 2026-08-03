import { useQuery } from "@tanstack/react-query";
import { getLatestMonitoring } from "../services/dashboard";

export const useLatestMonitoring = (assetId: number) => {
  return useQuery({
    queryKey: ["latest-monitoring", assetId],
    queryFn: () => getLatestMonitoring(assetId),
    // Feature 1 requirement: auto-refresh every 5 seconds.
    refetchInterval: 5000,
    enabled: Number.isFinite(assetId) && assetId > 0,
  });
};
