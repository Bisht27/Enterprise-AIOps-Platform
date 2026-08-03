import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { QrCode } from "lucide-react";
import Layout from "../components/layout/Layout";
import AssetTable from "../components/assets/AssetTable";
import AssetFormModal, {
  type AssetFormValues,
} from "../components/assets/AssetFormModal";
import {
  useAssets,
  useCreateAsset,
  useUpdateAsset,
  useDeleteAsset,
} from "../hooks/useAssets";
import type { Asset } from "../services/asset";

export default function Assets() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useAssets();

  const createAsset = useCreateAsset();
  const updateAsset = useUpdateAsset();
  const deleteAsset = useDeleteAsset();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);

  const openAddModal = () => {
    setEditingAsset(null);
    setIsModalOpen(true);
  };

  const openEditModal = (asset: Asset) => {
    setEditingAsset(asset);
    setIsModalOpen(true);
  };

  const handleSave = async (values: AssetFormValues) => {
    if (editingAsset) {
      await updateAsset.mutateAsync({
        id: editingAsset.id!,
        asset: values,
      });
    } else {
      await createAsset.mutateAsync(values as Asset);
    }
    setIsModalOpen(false);
  };

  const handleDelete = async (asset: Asset) => {
    if (!asset.id) return;
    const confirmed = window.confirm(
      `Delete asset "${asset.asset_name}" (${asset.asset_tag})? This cannot be undone.`
    );
    if (!confirmed) return;
    await deleteAsset.mutateAsync(asset.id);
  };

  if (isLoading)
    return (
      <Layout>
        <h2>Loading Assets...</h2>
      </Layout>
    );

  if (isError || !data)
    return (
      <Layout>
        <h2>Failed to load assets.</h2>
      </Layout>
    );

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Assets</h1>

        <div className="flex gap-3">
          <button
            onClick={() => navigate("/assets/qr")}
            className="flex items-center gap-2 border border-slate-300 px-4 py-2 rounded-lg hover:bg-slate-50"
          >
            <QrCode size={18} />
            QR Labels
          </button>

          <button
            onClick={openAddModal}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Add Asset
          </button>
        </div>
      </div>

      <AssetTable
        assets={data}
        onEdit={openEditModal}
        onDelete={handleDelete}
        onViewQr={() => navigate("/assets/qr")}
      />

      <AssetFormModal
        isOpen={isModalOpen}
        asset={editingAsset}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        isSaving={createAsset.isPending || updateAsset.isPending}
      />
    </Layout>
  );
}
