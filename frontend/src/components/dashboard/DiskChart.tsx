import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
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

export default function DiskChart({ data }: Props) {
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
      disk: item.disk_usage,
    }));

  return (
    <div className="bg-white rounded-xl shadow-md p-5">
      <h2 className="text-xl font-semibold mb-4">Disk Usage</h2>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="time"
            interval="preserveStartEnd"
            minTickGap={40}
          />

          <YAxis domain={[0, 100]} />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="disk"
            stroke="#f59e0b"
            strokeWidth={3}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}