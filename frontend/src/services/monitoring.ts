import api from "./api";

export const getMonitoring = async () => {
  const response = await api.get("/monitoring/dashboard");
  return response.data;
};
