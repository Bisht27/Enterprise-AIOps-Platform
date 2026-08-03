import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { CountBreakdown } from "../../services/report";

const STATUS_COLORS: Record<string, string> = {
  Critical: "#dc2626",
  Warning: "#d97706",
  Info: "#2563eb",
  Open: "#2563eb",
  Closed: "#16a34a",
  Escalated: "#dc2626",
  High: "#dc2626",
  Medium: "#d97706",
  Low: "#16a34a",
};

interface Props {
  title: string;
  data: CountBreakdown[];
}

export default function StatusBarChart({ title, data }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-md p-5">
      <h3 className="text-lg font-semibold mb-3 text-gray-800">{title}</h3>
      {data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
          No data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((d, index) => (
                <Cell key={index} fill={STATUS_COLORS[d.label] || "#2563eb"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
