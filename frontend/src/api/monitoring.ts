import api from "./client";

export interface LiveMonitoring {
  asset_id: number;
  hostname: string;
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  network_sent: number;
  network_received: number;
  uptime: number;
  last_seen: string;
}

export const getLiveMonitoring = async (): Promise<LiveMonitoring[]> => {
  const response = await api.get("/dashboard/live-monitoring");
  return response.data;
};
