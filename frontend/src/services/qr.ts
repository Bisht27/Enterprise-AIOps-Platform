import api from "./api";
import type { Asset } from "./asset";

const API_BASE = api.defaults.baseURL ?? "http://127.0.0.1:8000/api/v1";

export interface QrAssetListItem {
  id: number;
  asset_tag: string;
  asset_name: string;
  asset_type: string;
  location: string | null;
}

export interface QrScanResponse {
  asset: Asset;
  matched_by: "asset_id" | "asset_tag" | "serial_number";
}

// The image endpoints are plain <img>/download targets, not JSON —
// build the URL directly rather than fetching through axios.
// `version` is an optional cache-buster (e.g. Date.now()) so "Regenerate"
// can force the browser to re-request the image instead of reusing an
// old cached PNG -- the QR content itself is deterministic from the
// asset id, there's no server-side state to regenerate.
export const getAssetQrImageUrl = (assetId: number, version?: number) =>
  version
    ? `${API_BASE}/qr/assets/${assetId}?v=${version}`
    : `${API_BASE}/qr/assets/${assetId}`;

export const getAssetQrDownloadUrl = (assetId: number) =>
  `${API_BASE}/qr/assets/${assetId}/download`;

// The URL encoded inside the QR code, for "Copy QR URL" / preview. Built
// from window.location.origin so it always matches however this app is
// actually being accessed (localhost in dev, the real domain in prod).
export const getAssetDetailsUrl = (assetId: number) =>
  `${window.location.origin}/asset/${assetId}`;

export const listAssetsForQr = async (): Promise<QrAssetListItem[]> => {
  const response = await api.get<QrAssetListItem[]>("/qr/assets");
  return response.data;
};

export const scanQrCode = async (code: string): Promise<QrScanResponse> => {
  const response = await api.post<QrScanResponse>("/qr/scan", { code });
  return response.data;
};
