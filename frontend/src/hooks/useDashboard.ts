import { useQuery } from "@tanstack/react-query";
import { getDashboardSummary } from "../services/dashboard";

export interface DashboardData {
  total_assets: number;
  online_assets: number;
  offline_assets: number;
  total_alerts: number;
  open_alerts: number;
  critical_alerts: number;
  total_tickets: number;
  open_tickets: number;
  cpu_average: number;
  ram_average: number;
  disk_average: number;
}

export const useDashboard = () => {
  return useQuery<DashboardData>({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
    refetchInterval: 30000,
  });
};