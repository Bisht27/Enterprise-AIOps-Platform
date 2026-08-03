import { useMemo, useRef, useState } from "react";
import Layout from "../components/layout/Layout";
import { useQrAssetList, useScanQrCode } from "../hooks/useQr";
import {
  getAssetQrImageUrl,
  getAssetQrDownloadUrl,
  getAssetDetailsUrl,
  type QrAssetListItem,
  type QrScanResponse,
} from "../services/qr";

export default function QrAssets() {
  const { data: assets, isLoading, isError } = useQrAssetList();
  const scanMutation = useScanQrCode();

  const [scanCode, setScanCode] = useState("");
  const [scanResult, setScanResult] = useState<QrScanResponse | null>(null);
  const [scanErrorMsg, setScanErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Search / Filter Assets
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");

  // Regenerate QR -- the code is deterministic from the asset id, so
  // "regenerate" just forces a fresh image request (cache-bust) rather
  // than reusing a stale cached PNG.
  const [versions, setVersions] = useState<Record<number, number>>({});

  // Preview QR
  const [previewAsset, setPreviewAsset] = useState<QrAssetListItem | null>(
    null
  );
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const assetTypes = useMemo(() => {
    const types = new Set(
      (assets ?? []).map((a) => a.asset_type).filter(Boolean)
    );
    return Array.from(types).sort();
  }, [assets]);

  const locations = useMemo(() => {
    const locs = new Set(
      (assets ?? []).map((a) => a.location).filter(Boolean) as string[]
    );
    return Array.from(locs).sort();
  }, [assets]);

  const filteredAssets = useMemo(() => {
    if (!assets) return [];
    const term = search.trim().toLowerCase();
    return assets.filter((a) => {
      const matchesSearch =
        !term ||
        a.asset_tag.toLowerCase().includes(term) ||
        a.asset_name.toLowerCase().includes(term);
      const matchesType = !typeFilter || a.asset_type === typeFilter;
      const matchesLocation = !locationFilter || a.location === locationFilter;
      return matchesSearch && matchesType && matchesLocation;
    });
  }, [assets, search, typeFilter, locationFilter]);

  const handleScanSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanCode.trim()) return;

    setScanErrorMsg(null);
    setScanResult(null);

    try {
      const result = await scanMutation.mutateAsync(scanCode.trim());
      setScanResult(result);
    } catch (err: any) {
      setScanErrorMsg(
        err?.response?.data?.detail ?? "No asset matches that code."
      );
    } finally {
      setScanCode("");
      inputRef.current?.focus();
    }
  };

  const handlePrintAll = () => {
    window.print();
  };

  const handleRegenerate = (assetId: number) => {
    setVersions((prev) => ({ ...prev, [assetId]: Date.now() }));
  };

  const handleCopyUrl = async (assetId: number) => {
    const url = getAssetDetailsUrl(assetId);
    try {
      await navigator.clipboard.writeText(url);
      setCopiedId(assetId);
      setTimeout(() => setCopiedId((id) => (id === assetId ? null : id)), 1500);
    } catch {
      window.prompt("Copy the asset URL:", url);
    }
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6 print:hidden">
        <h1 className="text-3xl font-bold">QR Asset Management</h1>

        <button
          onClick={handlePrintAll}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          Print All QR Labels
        </button>
      </div>

      {/* Scan / lookup panel */}
      <div className="bg-white rounded-xl shadow p-6 mb-8 print:hidden">
        <h2 className="text-lg font-semibold mb-1">Scan or Enter a Code</h2>
        <p className="text-sm text-slate-500 mb-4">
          Works with a USB/Bluetooth barcode scanner (acts as a keyboard),
          or paste in the URL/text decoded from a QR code, an asset tag,
          or a serial number.
        </p>

        <form onSubmit={handleScanSubmit} className="flex gap-3">
          <input
            ref={inputRef}
            autoFocus
            value={scanCode}
            onChange={(e) => setScanCode(e.target.value)}
            placeholder="Scan or type asset code / URL..."
            className="flex-1 border rounded-lg p-2"
          />
          <button
            type="submit"
            disabled={scanMutation.isPending}
            className="bg-slate-800 hover:bg-slate-900 text-white px-5 py-2 rounded-lg disabled:opacity-50"
          >
            {scanMutation.isPending ? "Looking up..." : "Lookup"}
          </button>
        </form>

        {scanErrorMsg && (
          <div className="mt-4 rounded-lg bg-red-50 text-red-600 text-sm px-4 py-3">
            {scanErrorMsg}
          </div>
        )}

        {scanResult && (
          <div className="mt-4 rounded-lg bg-green-50 px-4 py-3 text-sm">
            <div className="font-semibold text-green-700 mb-1">
              Match found (by {scanResult.matched_by.replace("_", " ")})
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-slate-700">
              <div>
                <span className="font-medium">Asset Tag:</span>{" "}
                {scanResult.asset.asset_tag}
              </div>
              <div>
                <span className="font-medium">Name:</span>{" "}
                {scanResult.asset.asset_name}
              </div>
              <div>
                <span className="font-medium">Type:</span>{" "}
                {scanResult.asset.asset_type}
              </div>
              <div>
                <span className="font-medium">Status:</span>{" "}
                {scanResult.asset.status}
              </div>
              <div>
                <span className="font-medium">Location:</span>{" "}
                {scanResult.asset.location}
              </div>
              <div>
                <span className="font-medium">Health:</span>{" "}
                {scanResult.asset.health_status}
              </div>
            </div>
            {scanResult.asset.id != null && (
              <a
                href={`/asset/${scanResult.asset.id}`}
                className="inline-block mt-3 text-blue-600 hover:underline"
              >
                Open full asset details -&gt;
              </a>
            )}
          </div>
        )}
      </div>

      {/* Search / Filter Assets */}
      <div className="bg-white rounded-xl shadow p-4 mb-6 flex flex-wrap gap-3 print:hidden">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by asset tag or name..."
          className="flex-1 min-w-[200px] border rounded-lg p-2"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border rounded-lg p-2"
        >
          <option value="">All Types</option>
          {assetTypes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={locationFilter}
          onChange={(e) => setLocationFilter(e.target.value)}
          className="border rounded-lg p-2"
        >
          <option value="">All Locations</option>
          {locations.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </div>

      {/* QR label grid */}
      {isLoading && <p className="text-slate-500">Loading assets...</p>}
      {isError && (
        <p className="text-red-500">Failed to load assets for QR codes.</p>
      )}

      {assets && assets.length === 0 && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">
          No active assets yet. Add assets first to generate QR labels.
        </div>
      )}

      {assets && assets.length > 0 && filteredAssets.length === 0 && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500 print:hidden">
          No assets match your search/filters.
        </div>
      )}

      {filteredAssets.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6 print:grid-cols-3">
          {filteredAssets.map((asset) => (
            <div
              key={asset.id}
              className="bg-white rounded-xl shadow p-4 flex flex-col items-center text-center break-inside-avoid"
            >
              <button
                type="button"
                onClick={() => setPreviewAsset(asset)}
                className="print:pointer-events-none"
                title="Click to preview"
              >
                <img
                  src={getAssetQrImageUrl(asset.id, versions[asset.id])}
                  alt={`QR code for ${asset.asset_tag}`}
                  className="w-32 h-32 mb-3"
                />
              </button>
              <div className="font-semibold text-sm">{asset.asset_tag}</div>
              <div className="text-xs text-slate-500 mb-3">
                {asset.asset_name}
              </div>

              <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 print:hidden">
                <a
                  href={getAssetQrDownloadUrl(asset.id)}
                  download
                  className="text-xs text-blue-600 hover:underline"
                >
                  Download PNG
                </a>
                <button
                  onClick={() => window.print()}
                  className="text-xs text-slate-600 hover:underline"
                >
                  Print
                </button>
                <button
                  onClick={() => handleCopyUrl(asset.id)}
                  className="text-xs text-slate-600 hover:underline"
                >
                  {copiedId === asset.id ? "Copied!" : "Copy URL"}
                </button>
                <button
                  onClick={() => handleRegenerate(asset.id)}
                  className="text-xs text-slate-600 hover:underline"
                >
                  Regenerate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview modal */}
      {previewAsset && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 print:hidden"
          onClick={() => setPreviewAsset(null)}
        >
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold mb-1">
              {previewAsset.asset_name}
            </h3>
            <p className="text-sm text-slate-500 mb-4">
              {previewAsset.asset_tag}
            </p>

            <img
              src={getAssetQrImageUrl(previewAsset.id, versions[previewAsset.id])}
              alt={`QR code for ${previewAsset.asset_tag}`}
              className="w-56 h-56 mx-auto mb-4"
            />

            <p className="text-xs text-slate-400 break-all mb-4">
              {getAssetDetailsUrl(previewAsset.id)}
            </p>

            <div className="flex justify-center gap-3 flex-wrap">
              <a
                href={getAssetQrDownloadUrl(previewAsset.id)}
                download
                className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Download
              </a>
              <button
                onClick={() => handleCopyUrl(previewAsset.id)}
                className="text-sm bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg"
              >
                {copiedId === previewAsset.id ? "Copied!" : "Copy URL"}
              </button>
              <button
                onClick={() => setPreviewAsset(null)}
                className="text-sm border border-slate-300 px-4 py-2 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
