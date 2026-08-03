import { useQuery } from "@tanstack/react-query";
import { getAlerts } from "../services/alert";

export interface Alert {
  id: number;
  asset_id: number;
  alert_type: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
}

export const useAlerts = () =>
  useQuery<Alert[]>({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 30000,
  });