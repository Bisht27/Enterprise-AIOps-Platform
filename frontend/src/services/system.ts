import api from "./api";

export interface ConfigStatus {
  email: { configured: boolean; host: string | null; username: string | null; from: string };
  whatsapp: { provider: string; configured: boolean; business_number: string | null };
  sms: { configured: boolean; from_number: string | null };
  scheduler: { enabled: boolean; offline_threshold_minutes: number };
  admin_alerts: { configured: boolean; recipient_count: number };
  system_webhook: { token_set: boolean };
  retry_count: number;
  notification_timeout_seconds: number;
}

export interface AuditLogItem {
  id: number;
  user_id: number | null;
  action: string;
  target: string | null;
  detail: string | null;
  created_at: string;
}

export const getConfigStatus = async (): Promise<ConfigStatus> => {
  const response = await api.get("/system/config-status");
  return response.data;
};

export const getAuditLogs = async (): Promise<AuditLogItem[]> => {
  const response = await api.get("/audit");
  return response.data;
};
