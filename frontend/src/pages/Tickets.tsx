import { useState } from "react";
import Layout from "../components/layout/Layout";
import { useTickets, useResolveTicket, useDeleteTicket } from "../hooks/useTickets";

export default function Tickets() {
  const { data, isLoading, isError, refetch, isFetching } = useTickets();
  const resolveMutation = useResolveTicket();
  const deleteMutation = useDeleteTicket();

  // Tracks which row's action is in flight + any error, so multiple
  // rows can be acted on independently without one spinner blocking
  // the whole table.
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) return <h2>Loading Tickets...</h2>;
  if (isError || !data) return <h2>Failed to load tickets.</h2>;

  const handleResolve = (ticketId: number) => {
    setActionError(null);
    resolveMutation.mutate(ticketId, {
      onError: () =>
        setActionError(`Failed to resolve ticket #${ticketId}. Please try again.`),
    });
  };

  const handleDelete = (ticketId: number) => {
    if (!window.confirm(`Delete ticket #${ticketId}? This cannot be undone.`)) {
      return;
    }
    setActionError(null);
    deleteMutation.mutate(ticketId, {
      onError: () =>
        setActionError(`Failed to delete ticket #${ticketId}. Please try again.`),
    });
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Tickets</h1>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {isFetching ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {actionError && (
        <div className="mb-4 rounded-lg bg-red-50 text-red-700 px-4 py-2 text-sm">
          {actionError}
        </div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100">
            <tr>
              <th className="p-3">ID</th>
              <th className="p-3">Asset</th>
              <th className="p-3">Title</th>
              <th className="p-3">Priority</th>
              <th className="p-3">Status</th>
              <th className="p-3">Created</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>

          <tbody>
            {data.map((ticket) => {
              const isResolved = ["resolved", "closed"].includes(
                ticket.status.toLowerCase()
              );
              const isResolving =
                resolveMutation.isPending &&
                resolveMutation.variables === ticket.id;
              const isDeleting =
                deleteMutation.isPending &&
                deleteMutation.variables === ticket.id;

              return (
                <tr key={ticket.id} className="border-t">
                  <td className="p-3">{ticket.id}</td>
                  <td className="p-3">{ticket.asset_id}</td>
                  <td className="p-3">{ticket.title}</td>
                  <td className="p-3">{ticket.priority}</td>
                  <td className="p-3">{ticket.status}</td>
                  <td className="p-3">
                    {new Date(ticket.created_at).toLocaleString()}
                  </td>
                  <td className="p-3 space-x-3">
                    <button
                      onClick={() => handleResolve(ticket.id)}
                      disabled={isResolved || isResolving}
                      className="text-green-600 hover:text-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isResolving ? "Resolving..." : "Resolve"}
                    </button>
                    <button
                      onClick={() => handleDelete(ticket.id)}
                      disabled={isDeleting}
                      className="text-red-600 hover:text-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isDeleting ? "Deleting..." : "Delete"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}