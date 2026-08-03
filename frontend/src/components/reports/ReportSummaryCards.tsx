import type { DashboardReport } from "../../services/report";

const Card = ({ title, value }: { title: string; value: string | number }) => (
  <div className="bg-white rounded-lg shadow p-5">
    <h3 className="text-gray-500 text-xs uppercase tracking-wide">{title}</h3>
    <p className="text-2xl font-bold mt-1 text-gray-800">{value}</p>
  </div>
);

export default function ReportSummaryCards({ data }: { data: DashboardReport }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      <Card title="Total Assets" value={data.total_assets} />
      <Card title="Online Assets" value={data.online_assets} />
      <Card title="Offline Assets" value={data.offline_assets} />
      <Card title="Healthy Assets" value={data.healthy_assets} />
      <Card title="Critical Assets" value={data.critical_assets} />

      <Card title="Total Alerts" value={data.total_alerts} />
      <Card title="Critical Alerts" value={data.critical_alerts} />
      <Card title="Warning Alerts" value={data.warning_alerts} />
      <Card title="Open Tickets" value={data.open_tickets} />
      <Card title="Closed Tickets" value={data.closed_tickets} />

      <Card title="Avg CPU Usage" value={`${data.avg_cpu_usage}%`} />
      <Card title="Avg RAM Usage" value={`${data.avg_ram_usage}%`} />
      <Card title="Avg Disk Usage" value={`${data.avg_disk_usage}%`} />
      <Card title="Availability" value={`${data.asset_availability_pct}%`} />
      <Card title="Monthly Incidents" value={data.monthly_incidents} />
    </div>
  );
}
