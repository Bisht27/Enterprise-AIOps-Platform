import {
  useAssetAnomalies,
  useAssetForecast,
  useAssetHealthScore,
} from "../../hooks/useMl";

const riskColor: Record<string, string> = {
  low: "text-green-600 bg-green-50",
  medium: "text-yellow-600 bg-yellow-50",
  high: "text-red-600 bg-red-50",
  unknown: "text-slate-500 bg-slate-50",
};

const trendLabel: Record<string, string> = {
  increasing: "↑ increasing",
  decreasing: "↓ decreasing",
  stable: "→ stable",
};

interface Props {
  assetId: number;
}

export default function AiInsights({ assetId }: Props) {
  const { data: health, isLoading: healthLoading } =
    useAssetHealthScore(assetId);
  const { data: anomalies, isLoading: anomaliesLoading } =
    useAssetAnomalies(assetId);
  const { data: forecast, isLoading: forecastLoading } =
    useAssetForecast(assetId, 5);

  const isLoading = healthLoading || anomaliesLoading || forecastLoading;

  return (
    <div className="bg-white rounded-xl shadow-md p-5 mt-6">
      <h2 className="text-xl font-semibold mb-4">AI Insights</h2>

      {isLoading && (
        <p className="text-slate-500 text-sm">Analyzing telemetry...</p>
      )}

      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Health Score */}
          <div className="border rounded-lg p-4">
            <div className="text-sm text-slate-500 mb-1">Health Score</div>
            {health?.message ? (
              <p className="text-xs text-slate-400">{health.message}</p>
            ) : (
              <>
                <div className="text-3xl font-bold">
                  {health?.health_score}
                  <span className="text-base font-normal text-slate-400">
                    {" "}
                    / 100
                  </span>
                </div>
                <span
                  className={`inline-block mt-2 text-xs font-semibold px-2 py-1 rounded-full ${
                    riskColor[health?.risk_level ?? "unknown"]
                  }`}
                >
                  {health?.risk_level?.toUpperCase()} RISK
                </span>
              </>
            )}
          </div>

          {/* Anomalies */}
          <div className="border rounded-lg p-4">
            <div className="text-sm text-slate-500 mb-1">
              Anomaly Detection
            </div>
            {anomalies?.message ? (
              <p className="text-xs text-slate-400">{anomalies.message}</p>
            ) : (
              <>
                <div className="text-3xl font-bold">
                  {anomalies?.anomalies_found}
                  <span className="text-base font-normal text-slate-400">
                    {" "}
                    / {anomalies?.sample_size}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  data points flagged as unusual
                </p>
              </>
            )}
          </div>

          {/* Forecast Trend */}
          <div className="border rounded-lg p-4">
            <div className="text-sm text-slate-500 mb-1">Usage Trend</div>
            {forecast?.message ? (
              <p className="text-xs text-slate-400">{forecast.message}</p>
            ) : (
              <div className="space-y-1 text-sm">
                <div>
                  CPU:{" "}
                  <span className="font-medium">
                    {trendLabel[forecast?.trend?.cpu ?? "stable"]}
                  </span>
                </div>
                <div>
                  RAM:{" "}
                  <span className="font-medium">
                    {trendLabel[forecast?.trend?.ram ?? "stable"]}
                  </span>
                </div>
                <div>
                  Disk:{" "}
                  <span className="font-medium">
                    {trendLabel[forecast?.trend?.disk ?? "stable"]}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
