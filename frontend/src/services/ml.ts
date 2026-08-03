import api from "./api";

export interface AnomalyPoint {
  id: number;
  created_at: string;
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  is_anomaly: boolean;
  anomaly_score: number;
}

export interface AnomalyResponse {
  asset_id: number;
  sample_size: number;
  anomalies_found: number;
  points: AnomalyPoint[];
  message: string | null;
}

export interface ForecastPoint {
  step: number;
  label: string;
  predicted_cpu_usage: number;
  predicted_ram_usage: number;
  predicted_disk_usage: number;
}

export interface ForecastResponse {
  asset_id: number;
  sample_size: number;
  horizon: number;
  forecast: ForecastPoint[];
  trend: { cpu?: string; ram?: string; disk?: string };
  message: string | null;
}

export interface HealthScoreResponse {
  asset_id: number;
  health_score: number;
  risk_level: "low" | "medium" | "high" | "unknown";
  factors: {
    avg_cpu_usage?: number;
    avg_ram_usage?: number;
    avg_disk_usage?: number;
    open_alerts?: number;
    recent_anomalies?: number;
    sample_size?: number;
  };
  message: string | null;
}

export const getAssetAnomalies = async (
  assetId: number
): Promise<AnomalyResponse> => {
  const response = await api.get(`/ml/assets/${assetId}/anomalies`);
  return response.data;
};

export const getAssetForecast = async (
  assetId: number,
  horizon = 5
): Promise<ForecastResponse> => {
  const response = await api.get(`/ml/assets/${assetId}/forecast`, {
    params: { horizon },
  });
  return response.data;
};

export const getAssetHealthScore = async (
  assetId: number
): Promise<HealthScoreResponse> => {
  const response = await api.get(`/ml/assets/${assetId}/health-score`);
  return response.data;
};
