import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

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

export default function NetworkChart({ data }: Props) {
  const chartData = [...data]
    .sort(
      (a, b) =>
        new Date(a.created_at).getTime() -
        new Date(b.created_at).getTime()
    )
    .map((item) => ({
      time: new Date(item.created_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      sent: item.network_sent,
      received: item.network_received,
    }));

  return (
    <div className="bg-white rounded-xl shadow-md p-5">
      <h2 className="text-xl font-semibold mb-4">Network Traffic</h2>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="time"
            interval="preserveStartEnd"
            minTickGap={40}
          />

          <YAxis />

          <Tooltip />

          <Legend />

          <Line
            type="monotone"
            dataKey="sent"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={false}
          />

          <Line
            type="monotone"
            dataKey="received"
            stroke="#10b981"
            strokeWidth={3}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}