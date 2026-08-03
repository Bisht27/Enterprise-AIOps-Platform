import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getTickets, resolveTicket, deleteTicket } from "../services/ticket";

export interface Ticket {
  id: number;
  asset_id: number;
  title: string;
  description: string;
  priority: string;
  status: string;
  created_at: string;
}

export const useTickets = () =>
  useQuery<Ticket[]>({
    queryKey: ["tickets"],
    queryFn: getTickets,
    refetchInterval: 30000,
  });

export const useResolveTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticketId: number) => resolveTicket(ticketId),
    onSuccess: () => {
      // Refetch immediately so the table (and any alert/ticket counts
      // elsewhere on the dashboard) reflect the new status right away.
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });
};

export const useDeleteTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticketId: number) => deleteTicket(ticketId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });
};