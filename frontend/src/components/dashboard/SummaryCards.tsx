type DashboardData = {
  total_assets: number;
  online_assets: number;
  open_alerts: number;
};

type Props = {
  data: DashboardData;
};

const Card = ({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-gray-500 text-sm">{title}</h3>
    <p className="text-3xl font-bold mt-2">{value}</p>
  </div>
);

const SummaryCards = ({ data }: Props) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card title="Total Assets" value={data.total_assets} />
      <Card title="Online Assets" value={data.online_assets} />
      <Card title="Open Alerts" value={data.open_alerts} />
    </div>
  );
};

export default SummaryCards;