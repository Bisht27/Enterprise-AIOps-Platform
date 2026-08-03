import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Row {
  asset_name: string;
  [key: string]: unknown;
}

interface Props {
  title: string;
  data: Row[];
  dataKey: string;
  unit?: string;
  color?: string;
}

export default function TopAssetsChart({ title, data, dataKey, unit = "%", color = "#2563eb" }: Props) {
  const chartData = data.slice(0, 10).map((d) => ({
    name: d.asset_name.length > 14 ? `${d.asset_name.slice(0, 14)}...` : d.asset_name,
    value: d[dataKey] as number,
  }));

  return (
    <div className="bg-white rounded-xl shadow-md p-5">
      <h3 className="text-lg font-semibold mb-3 text-gray-800">{title}</h3>
      {chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
          No monitoring data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" unit={unit} />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip formatter={(v) => [`${v}${unit}`, title]} />
            <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
