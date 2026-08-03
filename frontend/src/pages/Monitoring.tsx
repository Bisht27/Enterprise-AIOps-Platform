import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Layout from "../components/layout/Layout";
import { useAssets, useAsset } from "../hooks/useAssets";
import { useMonitoringHistory, type MonitoringRange } from "../hooks/useMonitoringHistory";
import { useLatestMonitoring } from "../hooks/useMonitoring";
import CpuChart from "../components/dashboard/CpuChart";
import RamChart from "../components/dashboard/RamChart";
import DiskChart from "../components/dashboard/DiskChart";
import NetworkChart from "../components/dashboard/NetworkChart";
import MonitoringTable from "../components/dashboard/MonitoringTable";
import AiInsights from "../components/dashboard/AiInsights";

const RANGE_OPTIONS: { label: string; value: MonitoringRange | undefined }[] = [
  { label: "Last Hour", value: "1h" },
  { label: "Last 24 Hours", value: "24h" },
  { label: "Last 7 Days", value: "7d" },
];

function isRecentHeartbeat(lastSeen?: string | null) {
  if (!lastSeen) return false;
  return Date.now() - new Date(lastSeen).getTime() < 5 * 60 * 1000;
}

function HardwareField({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
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

export default function Monitoring() {
  const { data: assets, isLoading: assetsLoading } = useAssets();
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const [range, setRange] = useState<MonitoringRange | undefined>(undefined);

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
    refetch: refetchHistory,
    isFetching: historyFetching,
  } = useMonitoringHistory(selectedAssetId ?? 0, range);

  const online = asset
    ? asset.is_online && isRecentHeartbeat(asset.last_seen ?? undefined)
    : false;

  return (
    <Layout>
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <h1 className="text-3xl font-bold">Monitoring</h1>

        <div className="flex flex-wrap items-center gap-3">
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

          <button
            onClick={() => refetchHistory()}
            disabled={historyFetching}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
          >
            {historyFetching ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {!selectedAssetId && !assetsLoading && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">
          No assets to monitor yet. Add an asset first.
        </div>
      )}

      {selectedAssetId && (
        <>
          {/* Hardware & agent details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="bg-white rounded-xl shadow p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold">System</h2>
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
              <HardwareField label="Hostname" value={asset?.hostname} />
              <HardwareField
                label="Operating System"
                value={asset?.operating_system}
              />
              <HardwareField label="Platform" value={null} />
              <HardwareField label="Architecture" value={null} />
              <HardwareField
                label="Agent Version"
                value={asset?.agent_version}
              />
              <HardwareField
                label="Last Seen"
                value={
                  asset?.last_seen
                    ? new Date(asset.last_seen).toLocaleString()
                    : null
                }
              />
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <h2 className="text-lg font-semibold mb-3">CPU / Memory</h2>
              <HardwareField label="CPU Name" value={asset?.cpu_name} />
              <HardwareField label="CPU Cores" value={asset?.cpu_cores} />
              <HardwareField label="CPU Threads" value={asset?.cpu_threads} />
              <HardwareField label="CPU Frequency" value={null} />
              <HardwareField
                label="CPU Usage (live)"
                value={
                  latest ? `${Number(latest.cpu_usage).toFixed(1)}%` : null
                }
              />
              <HardwareField label="Installed RAM" value={asset?.ram_total} />
              <HardwareField
                label="RAM Usage (live)"
                value={
                  latest ? `${Number(latest.ram_usage).toFixed(1)}%` : null
                }
              />
              <HardwareField label="CPU Temperature" value={null} />
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <h2 className="text-lg font-semibold mb-3">Disk / Network</h2>
              <HardwareField label="Disk Total" value={asset?.disk_total} />
              <HardwareField label="Disk Used" value={asset?.disk_used} />
              <HardwareField label="Disk Free" value={asset?.disk_free} />
              <HardwareField
                label="Disk Usage (live)"
                value={
                  latest ? `${Number(latest.disk_usage).toFixed(1)}%` : null
                }
              />
              <HardwareField label="IP Address" value={asset?.private_ip} />
              <HardwareField label="MAC Address" value={asset?.mac_address} />
              <HardwareField label="GPU" value={null} />
            </div>
          </div>

          <p className="text-xs text-slate-400 mb-4">
            Platform, Architecture, CPU Frequency, CPU Temperature, and GPU
            are not collected by the monitoring agent yet -- shown as "Not
            available" until the agent is updated to report them.
          </p>

          {/* Time range filter */}
          <div className="flex gap-2 mb-4">
            {RANGE_OPTIONS.map((opt) => (
              <button
                key={opt.label}
                onClick={() => setRange(opt.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  range === opt.value
                    ? "bg-blue-600 text-white"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {historyLoading && (
            <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">
              Loading monitoring data...
            </div>
          )}

          {historyError && (
            <div className="bg-white rounded-xl shadow p-8 text-center text-red-500">
              No monitoring data found for this asset yet. Make sure the
              monitoring agent is running and reporting heartbeats.
            </div>
          )}

          {history && history.length === 0 && !historyLoading && (
            <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">
              No monitoring data in this time range.
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

              <MonitoringTable data={history} />

              <AiInsights assetId={selectedAssetId} />
            </>
          )}
        </>
      )}
    </Layout>
  );
}
