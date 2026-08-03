import type { ReactNode } from "react";
import { useParams, Link } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { useAsset } from "../hooks/useAssets";
import { useLatestMonitoring } from "../hooks/useMonitoring";
import { useMonitoringHistory } from "../hooks/useMonitoringHistory";
import CpuChart from "../components/dashboard/CpuChart";
import RamChart from "../components/dashboard/RamChart";
import DiskChart from "../components/dashboard/DiskChart";
import NetworkChart from "../components/dashboard/NetworkChart";

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="py-2 flex justify-between gap-4 border-b border-slate-100 last:border-b-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-medium text-slate-800 text-right">
        {value === null || value === undefined || value === "" ? (
          <span className="text-slate-400">—</span>
        ) : (
          value
        )}
      </span>
    </div>
  );
}

function isRecentHeartbeat(lastSeen?: string | null) {
  if (!lastSeen) return false;
  const diffMs = Date.now() - new Date(lastSeen).getTime();
  return diffMs < 5 * 60 * 1000; // within 5 minutes
}

export default function AssetDetails() {
  const { id } = useParams<{ id: string }>();
  const assetId = Number(id);

  const { data: asset, isLoading, isError } = useAsset(assetId);
  const { data: latest } = useLatestMonitoring(assetId);
  const { data: history } = useMonitoringHistory(assetId);

  if (isLoading) {
    return (
      <Layout>
        <p className="text-slate-500">Loading asset...</p>
      </Layout>
    );
  }

  if (isError || !asset) {
    return (
      <Layout>
        <div className="bg-white rounded-xl shadow p-8 text-center">
          <h1 className="text-xl font-semibold text-red-600 mb-2">
            Asset not found
          </h1>
          <p className="text-slate-500 mb-4">
            No asset exists with id "{id}". The QR sticker may point to a
            deleted or invalid asset.
          </p>
          <Link to="/assets" className="text-blue-600 hover:underline">
            Back to Assets
          </Link>
        </div>
      </Layout>
    );
  }

  const online = asset.is_online && isRecentHeartbeat(asset.last_seen ?? undefined);
  const historyData = history ?? [];

  return (
    <Layout>
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold">{asset.asset_name}</h1>
          <p className="text-slate-500">
            {asset.asset_tag} &middot; {asset.asset_type}
          </p>
        </div>

        <span
          className={`px-4 py-2 rounded-full text-sm font-semibold ${
            online
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {online ? "Online" : "Offline"}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Asset Information */}
        <div className="bg-white rounded-xl shadow p-6 lg:col-span-1">
          <h2 className="text-lg font-semibold mb-3">Asset Information</h2>
          <InfoRow label="Asset Name" value={asset.asset_name} />
          <InfoRow label="Asset Tag" value={asset.asset_tag} />
          <InfoRow label="Serial Number" value={asset.serial_number} />
          <InfoRow label="Manufacturer" value={asset.manufacturer} />
          <InfoRow label="Model" value={asset.model} />
          <InfoRow label="Status" value={asset.status} />
          <InfoRow label="Health" value={asset.health_status} />
          <InfoRow label="Location" value={asset.location} />
          <InfoRow
            label="Assigned User"
            value={asset.assigned_user_name}
          />
          <InfoRow
            label="Purchase Date"
            value={
              asset.purchase_date
                ? new Date(asset.purchase_date).toLocaleDateString()
                : null
            }
          />
          <InfoRow
            label="Warranty Expiry"
            value={
              asset.warranty_expiry
                ? new Date(asset.warranty_expiry).toLocaleDateString()
                : null
            }
          />
          <InfoRow
            label="Last Heartbeat"
            value={
              asset.last_seen
                ? new Date(asset.last_seen).toLocaleString()
                : null
            }
          />
        </div>

        {/* System / Network Information */}
        <div className="bg-white rounded-xl shadow p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-3">System &amp; Network</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
            <div>
              <InfoRow label="Hostname" value={asset.hostname} />
              <InfoRow label="Operating System" value={asset.operating_system} />
              <InfoRow label="CPU" value={asset.cpu_name} />
              <InfoRow
                label="CPU Cores / Threads"
                value={
                  asset.cpu_cores || asset.cpu_threads
                    ? `${asset.cpu_cores ?? "—"} / ${asset.cpu_threads ?? "—"}`
                    : null
                }
              />
              <InfoRow label="RAM" value={asset.ram_total} />
            </div>
            <div>
              <InfoRow label="Private IP" value={asset.private_ip} />
              <InfoRow label="Public IP" value={asset.public_ip} />
              <InfoRow label="MAC Address" value={asset.mac_address} />
              <InfoRow label="Disk Total" value={asset.disk_total} />
              <InfoRow
                label="Disk Used / Free"
                value={
                  asset.disk_used || asset.disk_free
                    ? `${asset.disk_used ?? "—"} / ${asset.disk_free ?? "—"}`
                    : null
                }
              />
            </div>
          </div>
        </div>
      </div>

      {/* Live snapshot */}
      {latest && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-xs text-slate-500">CPU</p>
            <p className="text-2xl font-bold">{latest.cpu_usage?.toFixed(1)}%</p>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-xs text-slate-500">RAM</p>
            <p className="text-2xl font-bold">{latest.ram_usage?.toFixed(1)}%</p>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-xs text-slate-500">Disk</p>
            <p className="text-2xl font-bold">{latest.disk_usage?.toFixed(1)}%</p>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <p className="text-xs text-slate-500">Last Update</p>
            <p className="text-sm font-semibold mt-2">
              {new Date(latest.created_at).toLocaleTimeString()}
            </p>
          </div>
        </div>
      )}

      {/* Per-asset graphs -- scoped to this asset's history only */}
      {historyData.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <CpuChart data={historyData} />
          <RamChart data={historyData} />
          <DiskChart data={historyData} />
          <NetworkChart data={historyData} />
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500 mt-6">
          No monitoring history yet for this asset.
        </div>
      )}
    </Layout>
  );
}
