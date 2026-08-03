import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import dashboardSocket from "../services/websocket";

export default function useDashboardSocket() {
  const queryClient = useQueryClient();

  useEffect(() => {
    dashboardSocket.connect((data) => {
      queryClient.setQueryData(["live-monitoring"], data.monitoring);
      queryClient.setQueryData(["dashboard-summary"], data.summary);
    });

    return () => dashboardSocket.disconnect();
  }, [queryClient]);
}