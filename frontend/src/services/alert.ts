import api from "./api";

export const getAlerts = async () => {
  const response = await api.get("/alerts");
  return response.data;
};
