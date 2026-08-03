import api from "./api";

export interface CountBreakdown {
  label: string;
  count: number;
}

export interface DashboardReport {
  total_assets: number;
  online_assets: number;
  offline_assets: number;
  healthy_assets: number;
  critical_assets: number;
  total_alerts: number;
  critical_alerts: number;
  warning_alerts: number;
  open_tickets: number;
  closed_tickets: number;
  avg_cpu_usage: number;
  avg_ram_usage: number;
  avg_disk_usage: number;
  asset_availability_pct: number;
  monthly_incidents: number;
  assets_by_type: CountBreakdown[];
  assets_by_location: CountBreakdown[];
  assets_by_os: CountBreakdown[];
}

export interface AlertReport {
  total: number;
  alerts_per_day: { date: string; count: number }[];
  by_severity: CountBreakdown[];
  avg_resolution_minutes: number;
  alerts: Record<string, unknown>[];
}

export interface TicketReport {
  total: number;
  by_status: CountBreakdown[];
  by_priority: CountBreakdown[];
  avg_resolution_hours: number;
  tickets: Record<string, unknown>[];
}

export interface PerformanceReport {
  per_asset: {
    asset_id: number;
    asset_name: string;
    avg_cpu: number;
    peak_cpu: number;
    avg_ram: number;
    peak_ram: number;
    avg_disk: number;
    peak_disk: number;
  }[];
  top_cpu: PerformanceReport["per_asset"];
  top_ram: PerformanceReport["per_asset"];
  top_disk: PerformanceReport["per_asset"];
}

export interface ExportHistoryItem {
  id: number;
  report_type: string;
  export_format: string;
  file_name: string;
  created_at: string;
}

export interface ScheduledReportItem {
  id: number;
  name: string;
  report_type: string;
  frequency: string;
  export_format: string;
  delivery_email: boolean;
  delivery_in_app: boolean;
  recipients?: string | null;
  is_active: boolean;
  created_at: string;
  last_run_at?: string | null;
  next_run_at?: string | null;
}

export interface ReportFilterParams {
  start_date?: string;
  end_date?: string;
  asset_type?: string;
  operating_system?: string;
  location?: string;
  severity?: string;
  priority?: string;
  asset_status?: string;
}

export const getDashboardReport = async (
  params: ReportFilterParams = {}
): Promise<DashboardReport> => {
  const response = await api.get("/reports/dashboard", { params });
  return response.data;
};

export const getAlertReport = async (
  params: ReportFilterParams = {}
): Promise<AlertReport> => {
  const response = await api.get("/reports/alerts", { params });
  return response.data;
};

export const getTicketReport = async (
  params: ReportFilterParams = {}
): Promise<TicketReport> => {
  const response = await api.get("/reports/tickets", { params });
  return response.data;
};

export const getPerformanceReport = async (
  params: ReportFilterParams = {}
): Promise<PerformanceReport> => {
  const response = await api.get("/reports/performance", { params });
  return response.data;
};

export const exportReport = async (
  reportType: string,
  format: "pdf" | "xlsx" | "csv" | "json",
  params: ReportFilterParams = {}
) => {
  const response = await api.get("/reports/export", {
    params: { report_type: reportType, format, ...params },
    responseType: "blob",
  });

  const disposition = response.headers["content-disposition"] as string | undefined;
  const match = disposition?.match(/filename="?([^"]+)"?/);
  const fileName = match?.[1] ?? `${reportType}_report.${format}`;

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const getExportHistory = async (): Promise<ExportHistoryItem[]> => {
  const response = await api.get("/reports/history");
  return response.data;
};

export const getScheduledReports = async (): Promise<ScheduledReportItem[]> => {
  const response = await api.get("/reports/schedule");
  return response.data;
};

export const createScheduledReport = async (data: {
  name: string;
  report_type: string;
  frequency: string;
  export_format: string;
  delivery_email: boolean;
  delivery_in_app: boolean;
  recipients?: string;
}): Promise<ScheduledReportItem> => {
  const response = await api.post("/reports/schedule", data);
  return response.data;
};

export const deleteScheduledReport = async (id: number) => {
  const response = await api.delete(`/reports/schedule/${id}`);
  return response.data;
};
