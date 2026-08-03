import { useEffect, useState } from "react";
import type { Asset } from "../../services/asset";

export type AssetFormValues = Omit<Asset, "id">;

interface AssetFormModalProps {
  isOpen: boolean;
  asset?: Asset | null;
  onClose: () => void;
  onSave: (asset: AssetFormValues) => void;
  isSaving?: boolean;
}

const emptyForm: AssetFormValues = {
  asset_tag: "",
  asset_name: "",
  asset_type: "",
  manufacturer: "",
  model: "",
  serial_number: "",
  hostname: "",
  ip_address: "",
  private_ip: "",
  public_ip: "",
  mac_address: "",
  operating_system: "",
  cpu_name: "",
  cpu_cores: 0,
  cpu_threads: 0,
  ram_total: "",
  disk_total: "",
  disk_used: "",
  disk_free: "",
  location: "",
  assigned_to: 0,
  purchase_date: null,
  warranty_expiry: null,
  health_status: "Healthy",
  status: "Available",
  agent_version: "",
  is_online: false,
};

export default function AssetFormModal({
  isOpen,
  asset,
  onClose,
  onSave,
  isSaving,
}: AssetFormModalProps) {
  const [formData, setFormData] = useState<AssetFormValues>(emptyForm);

  useEffect(() => {
    if (asset) {
      const { id, ...rest } = asset;
      setFormData({ ...emptyForm, ...rest });
    } else {
      setFormData(emptyForm);
    }
  }, [asset, isOpen]);

  if (!isOpen) return null;

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "number" ? Number(value) : value,
    }));
  };

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl w-[700px] p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6">
          {asset ? "Edit Asset" : "Add Asset"}
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <input
            name="asset_tag"
            placeholder="Asset Tag"
            className="border rounded-lg p-2"
            value={formData.asset_tag}
            onChange={handleChange}
          />
          <input
            name="asset_name"
            placeholder="Asset Name"
            className="border rounded-lg p-2"
            value={formData.asset_name}
            onChange={handleChange}
          />
          <input
            name="asset_type"
            placeholder="Asset Type"
            className="border rounded-lg p-2"
            value={formData.asset_type}
            onChange={handleChange}
          />
          <input
            name="manufacturer"
            placeholder="Manufacturer"
            className="border rounded-lg p-2"
            value={formData.manufacturer}
            onChange={handleChange}
          />
          <input
            name="model"
            placeholder="Model"
            className="border rounded-lg p-2"
            value={formData.model}
            onChange={handleChange}
          />
          <input
            name="serial_number"
            placeholder="Serial Number"
            className="border rounded-lg p-2"
            value={formData.serial_number}
            onChange={handleChange}
          />
          <input
            name="hostname"
            placeholder="Hostname"
            className="border rounded-lg p-2"
            value={formData.hostname}
            onChange={handleChange}
          />
          <input
            name="ip_address"
            placeholder="IP Address"
            className="border rounded-lg p-2"
            value={formData.ip_address}
            onChange={handleChange}
          />
          <input
            name="operating_system"
            placeholder="Operating System"
            className="border rounded-lg p-2"
            value={formData.operating_system}
            onChange={handleChange}
          />
          <input
            name="location"
            placeholder="Location"
            className="border rounded-lg p-2"
            value={formData.location}
            onChange={handleChange}
          />
          <input
            name="cpu_name"
            placeholder="CPU Name"
            className="border rounded-lg p-2"
            value={formData.cpu_name}
            onChange={handleChange}
          />
          <input
            type="number"
            name="cpu_cores"
            placeholder="CPU Cores"
            className="border rounded-lg p-2"
            value={formData.cpu_cores}
            onChange={handleChange}
          />
          <input
            name="ram_total"
            placeholder="RAM Total (e.g. 16GB)"
            className="border rounded-lg p-2"
            value={formData.ram_total}
            onChange={handleChange}
          />
          <input
            name="disk_total"
            placeholder="Disk Total (e.g. 512GB)"
            className="border rounded-lg p-2"
            value={formData.disk_total}
            onChange={handleChange}
          />

          <select
            name="status"
            className="border rounded-lg p-2"
            value={formData.status}
            onChange={handleChange}
          >
            <option value="Available">Available</option>
            <option value="Assigned">Assigned</option>
            <option value="Maintenance">Maintenance</option>
            <option value="Retired">Retired</option>
          </select>

          <select
            name="health_status"
            className="border rounded-lg p-2"
            value={formData.health_status}
            onChange={handleChange}
          >
            <option value="Healthy">Healthy</option>
            <option value="Warning">Warning</option>
            <option value="Critical">Critical</option>
          </select>
        </div>

        <div className="flex justify-end gap-3 mt-8">
          <button onClick={onClose} className="border px-5 py-2 rounded-lg">
            Cancel
          </button>

          <button
            onClick={handleSubmit}
            disabled={isSaving}
            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg disabled:opacity-50"
          >
            {isSaving ? "Saving..." : asset ? "Update" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
