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

export default function CpuChart({ data }: Props) {
  console.log("CPU Chart Data:", data);

  // Sort data by timestamp (oldest → newest)
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
      cpu: Number(item.cpu_usage.toFixed(2)),
    }));

  return (
    <div className="bg-white rounded-xl shadow-md p-5 mt-6">
      <h2 className="text-xl font-semibold mb-4">CPU Usage</h2>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="time"
            interval="preserveStartEnd"
            minTickGap={40}
          />

          <YAxis
            domain={[0, 100]}
            label={{
              value: "CPU %",
              angle: -90,
              position: "insideLeft",
            }}
          />

          <Tooltip
            formatter={(value) => [`${value}%`, "CPU Usage"]}
            />
          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#2563eb"
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}