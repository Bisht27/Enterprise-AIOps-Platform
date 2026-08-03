import { Link } from "react-router-dom";
import type { Asset } from "../../services/asset";

interface AssetTableProps {
  assets: Asset[];
  onEdit: (asset: Asset) => void;
  onDelete: (asset: Asset) => void;
  onViewQr: (asset: Asset) => void;
}

export default function AssetTable({
  assets,
  onEdit,
  onDelete,
  onViewQr,
}: AssetTableProps) {
  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <table className="w-full">
        <thead className="bg-slate-100">
          <tr>
            <th className="p-3 text-left">Asset Tag</th>
            <th className="p-3 text-left">Name</th>
            <th className="p-3 text-left">Hostname</th>
            <th className="p-3 text-left">IP Address</th>
            <th className="p-3 text-left">Status</th>
            <th className="p-3 text-left">Health</th>
            <th className="p-3 text-center">Actions</th>
          </tr>
        </thead>

        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id} className="border-t hover:bg-slate-50">
              <td className="p-3">{asset.asset_tag}</td>
              <td className="p-3">{asset.asset_name}</td>
              <td className="p-3">{asset.hostname}</td>
              <td className="p-3">{asset.ip_address}</td>
              <td className="p-3">{asset.status}</td>
              <td className="p-3">
                <span
                  className={
                    asset.health_status === "Healthy"
                      ? "text-green-600 font-semibold"
                      : asset.health_status === "Warning"
                      ? "text-yellow-600 font-semibold"
                      : "text-red-600 font-semibold"
                  }
                >
                  {asset.health_status}
                </span>
              </td>

              <td className="p-3 text-center space-x-3">
                <Link
                  to={`/asset/${asset.id}`}
                  className="text-blue-600 hover:underline"
                >
                  View
                </Link>
                <button
                  onClick={() => onViewQr(asset)}
                  className="text-slate-600 hover:underline"
                >
                  QR
                </button>
                <button
                  onClick={() => onEdit(asset)}
                  className="text-green-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(asset)}
                  className="text-red-600 hover:underline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
