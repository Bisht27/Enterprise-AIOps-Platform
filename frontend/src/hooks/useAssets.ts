import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getAssets,
  getAsset,
  createAsset,
  updateAsset,
  deleteAsset,
} from "../services/asset";

export const useAssets = () => {
  return useQuery({
    queryKey: ["assets"],
    queryFn: getAssets,
  });
};

export const useAsset = (id: number) => {
  return useQuery({
    queryKey: ["asset", id],
    queryFn: () => getAsset(id),
    enabled: Number.isFinite(id) && id > 0,
  });
};

export const useCreateAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["assets"],
      });
    },
  });
};

export const useUpdateAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, asset }: { id: number; asset: unknown }) =>
  updateAsset(id, asset as any),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["assets"],
      });
    },
  });
};

export const useDeleteAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["assets"],
      });
    },
  });
};