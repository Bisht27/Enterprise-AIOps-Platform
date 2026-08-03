interface StatCardProps {
  title: string;
  value: number | string;
  color: string;
}

export default function StatCard({
  title,
  value,
  color,
}: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md p-6 border-l-4"
         style={{ borderColor: color }}>
      <h3 className="text-gray-500 text-sm">{title}</h3>

      <p className="text-3xl font-bold mt-2">
        {value}
      </p>
    </div>
  );
}