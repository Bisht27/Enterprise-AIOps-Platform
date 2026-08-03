import api from "./api";

export const getTickets = async () => {
  const response = await api.get("/tickets");
  return response.data;
};

export const resolveTicket = async (ticketId: number) => {
  const response = await api.put(`/tickets/${ticketId}/resolve`);
  return response.data;
};

export const deleteTicket = async (ticketId: number) => {
  const response = await api.delete(`/tickets/${ticketId}`);
  return response.data;
};
