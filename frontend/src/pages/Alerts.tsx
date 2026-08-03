import Layout from "../components/layout/Layout";
import { useAlerts } from "../hooks/useAlerts";

export default function Alerts() {
  const { data, isLoading, isError, refetch, isFetching } = useAlerts();

  if (isLoading)
    return (
      <Layout>
        <h2>Loading Alerts...</h2>
      </Layout>
    );
  if (isError || !data)
    return (
      <Layout>
        <h2>Failed to load alerts.</h2>
      </Layout>
    );

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Alerts</h1>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {isFetching ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-100">
            <tr>
              <th className="p-3">ID</th>
              <th className="p-3">Asset</th>
              <th className="p-3">Type</th>
              <th className="p-3">Severity</th>
              <th className="p-3">Message</th>
              <th className="p-3">Status</th>
              <th className="p-3">Created</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>

          <tbody>
            {data.map((alert) => (
              <tr key={alert.id} className="border-t">
                <td className="p-3">{alert.id}</td>
                <td className="p-3">{alert.asset_id}</td>
                <td className="p-3">{alert.alert_type}</td>
                <td className="p-3">
                  <span
                    className={
                      alert.severity === "Critical"
                        ? "text-red-600 font-bold"
                        : "text-yellow-600 font-bold"
                    }
                  >
                    {alert.severity}
                  </span>
                </td>
                <td className="p-3">{alert.message}</td>
                <td className="p-3">{alert.status}</td>
                <td className="p-3">
                  {new Date(alert.created_at).toLocaleString()}
                </td>
                <td className="p-3 space-x-2">
                  <button className="text-green-600">
                    Resolve
                  </button>

                  <button className="text-red-600">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}