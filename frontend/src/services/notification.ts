import api from "./api";

export interface NotificationItem {
  id: number;
  event_type: string;
  severity: "Critical" | "Warning" | "Info" | string;
  title: string;
  message: string;
  asset_id?: number | null;
  alert_id?: number | null;
  ticket_id?: number | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface DeliveryItem {
  id: number;
  notification_id: number;
  channel: "email" | "whatsapp" | "in_app" | string;
  recipient: string;
  status: "Pending" | "Sent" | "Delivered" | "Failed" | "Retrying" | string;
  provider?: string | null;
  error?: string | null;
  latency_ms?: number | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferences {
  user_id: number;
  email_enabled: boolean;
  whatsapp_enabled: boolean;
  in_app_enabled: boolean;
  slack_enabled: boolean;
  teams_enabled: boolean;
  sms_enabled: boolean;
  critical_alerts: boolean;
  warning_alerts: boolean;
  offline_alerts: boolean;
  ticket_notifications: boolean;
  maintenance_alerts: boolean;
  security_alerts: boolean;
  daily_summary: boolean;
  weekly_summary: boolean;
  whatsapp_number?: string | null;
  slack_webhook_url?: string | null;
  teams_webhook_url?: string | null;
  sms_number?: string | null;
}

export const getNotifications = async (): Promise<NotificationItem[]> => {
  const response = await api.get("/notifications");
  return response.data;
};

export const getUnreadCount = async (): Promise<number> => {
  const response = await api.get("/notifications/unread-count");
  return response.data.unread_count;
};

export const markNotificationRead = async (id: number) => {
  const response = await api.put(`/notifications/${id}/read`);
  return response.data;
};

export const getDeliveryHistory = async (): Promise<DeliveryItem[]> => {
  const response = await api.get("/notifications/history");
  return response.data;
};

export const retryDelivery = async (deliveryId: number) => {
  const response = await api.post("/notifications/retry", null, {
    params: { delivery_id: deliveryId },
  });
  return response.data;
};

export const getPreferences = async (): Promise<NotificationPreferences> => {
  const response = await api.get("/notifications/preferences");
  return response.data;
};

export const updatePreferences = async (
  data: Partial<NotificationPreferences>
): Promise<NotificationPreferences> => {
  const response = await api.put("/notifications/preferences", data);
  return response.data;
};

export const sendTestEmail = async (to_email: string) => {
  const response = await api.post("/notifications/test/email", { to_email });
  return response.data;
};

export const sendTestWhatsApp = async (to_number: string) => {
  const response = await api.post("/notifications/test/whatsapp", { to_number });
  return response.data;
};

export const sendTestSlack = async (webhook_url: string) => {
  const response = await api.post("/notifications/test/slack", { webhook_url });
  return response.data;
};

export const sendTestTeams = async (webhook_url: string) => {
  const response = await api.post("/notifications/test/teams", { webhook_url });
  return response.data;
};

export const sendTestSms = async (to_number: string) => {
  const response = await api.post("/notifications/test/sms", { to_number });
  return response.data;
};
