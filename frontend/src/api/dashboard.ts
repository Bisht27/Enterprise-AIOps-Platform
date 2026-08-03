import api from "./client";

export interface DashboardSummary {
  total_assets: number;
  online_assets: number;
  offline_assets: number;
  total_alerts: number;
  open_alerts: number;
  critical_alerts: number;
  total_tickets: number;
  open_tickets: number;
}

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await api.get("/dashboard/summary");
  return response.data;
};