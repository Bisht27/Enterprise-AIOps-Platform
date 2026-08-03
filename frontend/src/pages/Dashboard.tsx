import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Layout from "../components/layout/Layout";
import SummaryCards from "../components/dashboard/SummaryCards";
import CpuChart from "../components/dashboard/CpuChart";
import RamChart from "../components/dashboard/RamChart";
import DiskChart from "../components/dashboard/DiskChart";
import NetworkChart from "../components/dashboard/NetworkChart";
import MonitoringTable from "../components/dashboard/MonitoringTable";
import { useDashboard } from "../hooks/useDashboard";
import { useAssets, useAsset } from "../hooks/useAssets";
import { useMonitoringHistory } from "../hooks/useMonitoringHistory";
import { useLatestMonitoring } from "../hooks/useMonitoring";
import { useAlerts } from "../hooks/useAlerts";

function isRecentHeartbeat(lastSeen?: string | null) {
  if (!lastSeen) return false;
  return Date.now() - new Date(lastSeen).getTime() < 5 * 60 * 1000;
}

function InfoField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="py-2 flex justify-between gap-4 border-b border-slate-100 last:border-b-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-medium text-slate-800 text-right">
        {value === null || value === undefined || value === "" ? (
          <span className="text-slate-400">Not available</span>
        ) : (
          value
        )}
      </span>
    </div>
  );
}

const Dashboard = () => {
  const { data, isLoading, error } = useDashboard();

  // Asset selection for the live monitoring panel -- Monitoring is now
  // part of the Dashboard instead of a separate page/workflow.
  const { data: assets, isLoading: assetsLoading } = useAssets();
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedAssetId && assets && assets.length > 0) {
      setSelectedAssetId(assets[0].id);
    }
  }, [assets, selectedAssetId]);

  const { data: asset } = useAsset(selectedAssetId ?? 0);
  const { data: latest } = useLatestMonitoring(selectedAssetId ?? 0);
  const {
    data: history,
    isLoading: historyLoading,
    isError: historyError,
  } = useMonitoringHistory(selectedAssetId ?? 0);

  // Reuse the existing alerts API/hook -- filter down to the selected
  // asset's currently open alerts instead of adding a new endpoint.
  const { data: allAlerts } = useAlerts();
  const assetAlerts = (allAlerts ?? []).filter(
    (a) => a.asset_id === selectedAssetId && a.status === "Open"
  );

  const online = asset
    ? asset.is_online && isRecentHeartbeat(asset.last_seen ?? undefined)
    : false;

  if (isLoading) return <h2>Loading...</h2>;
  if (error) return <h2>Error loading dashboard</h2>;
  if (!data) return <h2>No data found</h2>;

  return (
    <Layout>
      <SummaryCards data={data} />

      <div className="flex flex-wrap justify-between items-center gap-4 mt-8 mb-4">
        <h2 className="text-2xl font-bold">Live Monitoring</h2>

        <select
          className="border rounded-lg p-2 bg-white"
          value={selectedAssetId ?? ""}
          onChange={(e) => setSelectedAssetId(Number(e.target.value))}
          disabled={assetsLoading || !assets?.length}
        >
          {assetsLoading && <option>Loading assets...</option>}
          {!assetsLoading && !assets?.length && (
            <option>No assets available</option>
          )}
          {assets?.map((a: any) => (
            <option key={a.id} value={a.id}>
              {a.asset_name ?? a.hostname ?? `Asset #${a.id}`}
            </option>
          ))}
        </select>
      </div>

      {!selectedAssetId && !assetsLoading && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">
          No assets to monitor yet. Add an asset first.
        </div>
      )}

      {selectedAssetId && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="bg-white rounded-xl shadow p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">System</h3>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    online
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {online ? "Online" : "Offline"}
                </span>
              </div>
              <InfoField label="Hostname" value={asset?.hostname} />
              <InfoField
                label="Operating System"
                value={asset?.operating_system}
              />
              <InfoField label="IP Address" value={asset?.private_ip} />
              <InfoField
                label="Last Heartbeat"
                value={
                  asset?.last_seen
                    ? new Date(asset.last_seen).toLocaleString()
                    : null
                }
              />
              <InfoField
                label="System Uptime"
                value={
                  latest?.uptime !== undefined && latest?.uptime !== null
                    ? `${(Number(latest.uptime) / 3600).toFixed(1)} hrs`
                    : null
                }
              />
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="text-lg font-semibold mb-3">Live Usage</h3>
              <InfoField
                label="CPU Usage"
                value={
                  latest ? `${Number(latest.cpu_usage).toFixed(1)}%` : null
                }
              />
              <InfoField
                label="RAM Usage"
                value={
                  latest ? `${Number(latest.ram_usage).toFixed(1)}%` : null
                }
              />
              <InfoField
                label="Disk Usage"
                value={
                  latest ? `${Number(latest.disk_usage).toFixed(1)}%` : null
                }
              />
              <InfoField
                label="Network Usage"
                value={
                  latest
                    ? `${(
                        ((latest.network_sent ?? 0) +
                          (latest.network_received ?? 0)) /
                        1_000_000
                      ).toFixed(2)} MB`
                    : null
                }
              />
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="text-lg font-semibold mb-3">Active Alerts</h3>
              {assetAlerts.length === 0 && (
                <p className="text-sm text-slate-400">No active alerts.</p>
              )}
              {assetAlerts.map((a) => (
                <div
                  key={a.id}
                  className="py-2 flex justify-between gap-4 border-b border-slate-100 last:border-b-0"
                >
                  <span className="text-sm text-slate-600">
                    {a.alert_type}
                  </span>
                  <span
                    className={`text-sm font-semibold ${
                      a.severity === "Critical"
                        ? "text-red-600"
                        : "text-yellow-600"
                    }`}
                  >
                    {a.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {historyLoading && (
            <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">
              Loading monitoring data...
            </div>
          )}

          {historyError && (
            <div className="bg-white rounded-xl shadow p-8 text-center text-red-500">
              No monitoring data found for this asset yet.
            </div>
          )}

          {history && history.length > 0 && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <CpuChart data={history} />
                <RamChart data={history} />
                <DiskChart data={history} />
                <NetworkChart data={history} />
              </div>

              <div className="mt-6">
                <MonitoringTable data={history} />
              </div>
            </>
          )}
        </>
      )}
    </Layout>
  );
};

export default Dashboard;
