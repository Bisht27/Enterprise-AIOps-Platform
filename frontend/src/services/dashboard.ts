import api from "./api";

export const getDashboardSummary = async () => {
  const response = await api.get("/dashboard/summary");
  return response.data;
};

export const getMonitoringHistory = async (
  assetId: number,
  range?: "1h" | "24h" | "7d"
) => {
  const response = await api.get(`/monitoring/history/${assetId}`, {
    params: range ? { range } : undefined,
  });
  return response.data;
};

export const getLatestMonitoring = async (assetId: number) => {
  const response = await api.get(`/monitoring/latest/${assetId}`);
  return response.data;
};
