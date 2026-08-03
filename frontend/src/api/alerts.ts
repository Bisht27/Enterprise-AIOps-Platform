import api from "./client";

export interface Alert {
  id: number;
  asset_id: number;
  alert_type: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
}

export const getAlerts = async (): Promise<Alert[]> => {
  const response = await api.get("/alerts");
  return response.data;
};

export const resolveAlert = async (id: number) => {
  return api.put(`/alerts/${id}/resolve`);
};

export const deleteAlert = async (id: number) => {
  return api.delete(`/alerts/${id}`);
};