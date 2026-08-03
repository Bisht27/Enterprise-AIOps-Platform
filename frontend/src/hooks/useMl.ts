import { useQuery } from "@tanstack/react-query";
import {
  getAssetAnomalies,
  getAssetForecast,
  getAssetHealthScore,
} from "../services/ml";

export const useAssetAnomalies = (assetId: number) => {
  return useQuery({
    queryKey: ["ml-anomalies", assetId],
    queryFn: () => getAssetAnomalies(assetId),
    enabled: !!assetId,
    refetchInterval: 60000,
  });
};

export const useAssetForecast = (assetId: number, horizon = 5) => {
  return useQuery({
    queryKey: ["ml-forecast", assetId, horizon],
    queryFn: () => getAssetForecast(assetId, horizon),
    enabled: !!assetId,
    refetchInterval: 60000,
  });
};

export const useAssetHealthScore = (assetId: number) => {
  return useQuery({
    queryKey: ["ml-health-score", assetId],
    queryFn: () => getAssetHealthScore(assetId),
    enabled: !!assetId,
    refetchInterval: 60000,
  });
};
