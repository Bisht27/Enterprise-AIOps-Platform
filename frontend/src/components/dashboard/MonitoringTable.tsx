interface HistoryItem {
  id: number;
  asset_id: number;
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  network_sent: number;
  network_received: number;
  created_at: string;
}

interface Props {
  data: HistoryItem[];
}

export default function MonitoringTable({ data }: Props) {
  const tableData = [...data]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() -
        new Date(a.created_at).getTime()
    )
    .slice(0, 10);

  return (
    <div className="bg-white rounded-xl shadow-md p-5 mt-6">
      <h2 className="text-xl font-semibold mb-4">
        Latest Monitoring
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th className="border p-3">Time</th>
              <th className="border p-3">CPU %</th>
              <th className="border p-3">RAM %</th>
              <th className="border p-3">Disk %</th>
              <th className="border p-3">Sent</th>
              <th className="border p-3">Received</th>
            </tr>
          </thead>

          <tbody>
            {tableData.map((item) => (
              <tr key={item.id} className="text-center hover:bg-gray-50">
                <td className="border p-2">
                  {new Date(item.created_at).toLocaleString()}
                </td>

                <td className="border p-2">
                  {item.cpu_usage.toFixed(1)}%
                </td>

                <td className="border p-2">
                  {item.ram_usage.toFixed(1)}%
                </td>

                <td className="border p-2">
                  {item.disk_usage.toFixed(1)}%
                </td>

                <td className="border p-2">
                  {item.network_sent.toLocaleString()}
                </td>

                <td className="border p-2">
                  {item.network_received.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}