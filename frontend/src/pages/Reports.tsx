import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Download, CalendarClock, RefreshCw, Trash2, Printer } from "lucide-react";

import Layout from "../components/layout/Layout";
import ReportSummaryCards from "../components/reports/ReportSummaryCards";
import BreakdownPieChart from "../components/reports/BreakdownPieChart";
import StatusBarChart from "../components/reports/StatusBarChart";
import AlertsTrendChart from "../components/reports/AlertsTrendChart";
import TopAssetsChart from "../components/reports/TopAssetsChart";

import {
  getDashboardReport,
  getAlertReport,
  getTicketReport,
  getPerformanceReport,
  exportReport,
  getExportHistory,
  getScheduledReports,
  createScheduledReport,
  deleteScheduledReport,
  type ReportFilterParams,
} from "../services/report";

const DATE_PRESETS: { label: string; days: number | null }[] = [
  { label: "Today", days: 0 },
  { label: "Last 7 Days", days: 7 },
  { label: "Last 30 Days", days: 30 },
  { label: "Last 90 Days", days: 90 },
  { label: "All Time", days: null },
];

function presetToRange(days: number | null): ReportFilterParams {
  if (days === null) return {};
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  return {
    start_date: start.toISOString(),
    end_date: end.toISOString(),
  };
}

export default function Reports() {
  const queryClient = useQueryClient();
  const [preset, setPreset] = useState("Last 30 Days");
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleForm, setScheduleForm] = useState({
    name: "",
    report_type: "dashboard",
    frequency: "Weekly",
    export_format: "pdf",
    delivery_email: true,
    delivery_in_app: false,
    recipients: "",
  });

  const filters = presetToRange(
    DATE_PRESETS.find((p) => p.label === preset)?.days ?? 30
  );

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ["reports", "dashboard", filters],
    queryFn: () => getDashboardReport(filters),
  });

  const { data: alertReport } = useQuery({
    queryKey: ["reports", "alerts", filters],
    queryFn: () => getAlertReport(filters),
  });

  const { data: ticketReport } = useQuery({
    queryKey: ["reports", "tickets", filters],
    queryFn: () => getTicketReport(filters),
  });

  const { data: performanceReport } = useQuery({
    queryKey: ["reports", "performance", filters],
    queryFn: () => getPerformanceReport(filters),
  });

  const { data: history = [] } = useQuery({
    queryKey: ["reports", "history"],
    queryFn: getExportHistory,
  });

  const { data: schedules = [] } = useQuery({
    queryKey: ["reports", "schedules"],
    queryFn: getScheduledReports,
  });

  const scheduleMutation = useMutation({
    mutationFn: createScheduledReport,
    onSuccess: () => {
      toast.success("Report scheduled");
      setScheduleOpen(false);
      queryClient.invalidateQueries({ queryKey: ["reports", "schedules"] });
    },
    onError: () => toast.error("Could not schedule report"),
  });

  const deleteScheduleMutation = useMutation({
    mutationFn: deleteScheduledReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", "schedules"] });
    },
  });

  const handleExport = async (reportType: string, format: "pdf" | "xlsx" | "csv" | "json") => {
    try {
      await exportReport(reportType, format, filters);
      toast.success(`${reportType} report exported as ${format.toUpperCase()}`);
      queryClient.invalidateQueries({ queryKey: ["reports", "history"] });
    } catch {
      toast.error("Export failed");
    }
  };

  return (
    <Layout>
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Reports &amp; Analytics</h1>

        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={preset}
            onChange={(e) => setPreset(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
          >
            {DATE_PRESETS.map((p) => (
              <option key={p.label} value={p.label}>
                {p.label}
              </option>
            ))}
          </select>

          <button
            onClick={() => handleExport("dashboard", "pdf")}
            className="flex items-center gap-1 bg-red-600 text-white px-3 py-2 rounded-md text-sm hover:bg-red-700"
          >
            <Download size={14} /> PDF
          </button>
          <button
            onClick={() => handleExport("dashboard", "xlsx")}
            className="flex items-center gap-1 bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700"
          >
            <Download size={14} /> Excel
          </button>
          <button
            onClick={() => handleExport("dashboard", "csv")}
            className="flex items-center gap-1 bg-gray-600 text-white px-3 py-2 rounded-md text-sm hover:bg-gray-700"
          >
            <Download size={14} /> CSV
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1 bg-white border border-gray-300 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-50"
          >
            <Printer size={14} /> Print
          </button>
          <button
            onClick={() => setScheduleOpen((o) => !o)}
            className="flex items-center gap-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700"
          >
            <CalendarClock size={14} /> Schedule Report
          </button>
        </div>
      </div>

      {scheduleOpen && (
        <div className="bg-white rounded-xl shadow p-6 mb-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">Schedule a Report</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <input
              placeholder="Report name"
              value={scheduleForm.name}
              onChange={(e) => setScheduleForm({ ...scheduleForm, name: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            />
            <select
              value={scheduleForm.report_type}
              onChange={(e) => setScheduleForm({ ...scheduleForm, report_type: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {["dashboard", "asset", "alert", "ticket", "performance", "security", "notification"].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <select
              value={scheduleForm.frequency}
              onChange={(e) => setScheduleForm({ ...scheduleForm, frequency: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"].map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
            <select
              value={scheduleForm.export_format}
              onChange={(e) => setScheduleForm({ ...scheduleForm, export_format: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {["pdf", "xlsx", "csv", "json"].map((f) => (
                <option key={f} value={f}>{f.toUpperCase()}</option>
              ))}
            </select>
            <input
              placeholder="Recipient emails (comma separated)"
              value={scheduleForm.recipients}
              onChange={(e) => setScheduleForm({ ...scheduleForm, recipients: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm sm:col-span-2 lg:col-span-3"
            />
            <button
              onClick={() => scheduleMutation.mutate(scheduleForm)}
              className="bg-blue-600 text-white rounded-md px-4 py-2 text-sm hover:bg-blue-700"
            >
              Save Schedule
            </button>
          </div>
          <p className="text-xs text-gray-400">
            Reports run automatically on the schedule above and are emailed to the recipients
            listed. Delivery is checked every 15 minutes, so the first run may lag slightly
            behind the exact scheduled time.
          </p>

          {schedules.length > 0 && (
            <ul className="divide-y divide-gray-100 border-t border-gray-100 pt-3">
              {schedules.map((s) => (
                <li key={s.id} className="flex items-center justify-between py-2 text-sm">
                  <span>
                    <span className="font-medium">{s.name}</span>{" "}
                    <span className="text-gray-400">
                      ({s.report_type}, {s.frequency}, {s.export_format.toUpperCase()})
                    </span>
                  </span>
                  <button
                    onClick={() => deleteScheduleMutation.mutate(s.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {dashboardLoading || !dashboard ? (
        <div className="bg-white rounded-xl shadow p-12 text-center text-gray-400">
          Loading report data...
        </div>
      ) : (
        <>
          <ReportSummaryCards data={dashboard} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <BreakdownPieChart title="Assets by Type" data={dashboard.assets_by_type} />
            <BreakdownPieChart title="Assets by OS" data={dashboard.assets_by_os} />
            <BreakdownPieChart title="Assets by Location" data={dashboard.assets_by_location} />
          </div>

          {alertReport && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <AlertsTrendChart data={alertReport.alerts_per_day} />
              <StatusBarChart title="Critical vs Warning Alerts" data={alertReport.by_severity} />
            </div>
          )}

          {ticketReport && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <StatusBarChart title="Tickets by Status" data={ticketReport.by_status} />
              <StatusBarChart title="Tickets by Priority" data={ticketReport.by_priority} />
            </div>
          )}

          {performanceReport && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
              <TopAssetsChart
                title="Top 10 Highest CPU"
                data={performanceReport.top_cpu}
                dataKey="peak_cpu"
                color="#dc2626"
              />
              <TopAssetsChart
                title="Top 10 Highest RAM"
                data={performanceReport.top_ram}
                dataKey="peak_ram"
                color="#d97706"
              />
              <TopAssetsChart
                title="Top 10 Highest Disk Usage"
                data={performanceReport.top_disk}
                dataKey="peak_disk"
                color="#7c3aed"
              />
            </div>
          )}

          <div className="bg-white rounded-xl shadow-md p-5 mt-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-800">Recent Reports</h3>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ["reports", "history"] })}
                className="text-gray-400 hover:text-gray-600"
              >
                <RefreshCw size={16} />
              </button>
            </div>
            {history.length === 0 ? (
              <p className="text-sm text-gray-400">No reports exported yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-200">
                    <th className="py-2 pr-4">File</th>
                    <th className="py-2 pr-4">Type</th>
                    <th className="py-2 pr-4">Format</th>
                    <th className="py-2 pr-4">Generated</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-gray-100">
                      <td className="py-2 pr-4">{h.file_name}</td>
                      <td className="py-2 pr-4 capitalize">{h.report_type}</td>
                      <td className="py-2 pr-4 uppercase">{h.export_format}</td>
                      <td className="py-2 pr-4">{new Date(h.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </Layout>
  );
}
