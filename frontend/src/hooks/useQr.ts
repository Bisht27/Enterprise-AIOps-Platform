import { useMutation, useQuery } from "@tanstack/react-query";
import { listAssetsForQr, scanQrCode } from "../services/qr";

export const useQrAssetList = () => {
  return useQuery({
    queryKey: ["qr-assets"],
    queryFn: listAssetsForQr,
  });
};

export const useScanQrCode = () => {
  return useMutation({
    mutationFn: (code: string) => scanQrCode(code),
  });
};
