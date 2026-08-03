
import api from "./api";
export interface Asset {
  id?: number;
  asset_tag: string;
  asset_name: string;
  asset_type: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  hostname: string;
  ip_address: string;
  private_ip: string;
  public_ip: string;
  mac_address: string;
  operating_system: string;
  cpu_name: string;
  cpu_cores: number;
  cpu_threads: number;
  ram_total: string;
  disk_total: string;
  disk_used: string;
  disk_free: string;
  location: string;
  assigned_to: number;
  purchase_date: string | null;
  warranty_expiry: string | null;
  health_status: string;
  status: string;
  agent_version: string;
  is_online: boolean;
  last_seen?: string | null;
  assigned_user_name?: string | null;
}

export const getAssets = async () => {
  const response = await api.get("/assets");
  return response.data;
};

export const getAsset = async (id: number): Promise<Asset> => {
  const response = await api.get(`/assets/${id}`);
  return response.data;
};

export const createAsset = async (asset: Asset) => {
  const response = await api.post("/assets", asset);
  return response.data;
};

export const updateAsset = async (id: number, asset: Asset) => {
  const response = await api.put(`/assets/${id}`, asset);
  return response.data;
};

export const deleteAsset = async (id: number) => {
  const response = await api.delete(`/assets/${id}`);
  return response.data;
};