import { useQuery } from "@tanstack/react-query";
import Layout from "../components/layout/Layout";
import { useAuth } from "../context/AuthContext";
import { getConfigStatus, getAuditLogs } from "../services/system";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
        ok ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-green-500" : "bg-gray-400"}`} />
      {label}
    </span>
  );
}

export default function Settings() {
  const { user, logout } = useAuth();

  // These are admin-only on the backend -- for non-admin users the
  // request 403s and the section below simply doesn't render.
  const { data: configStatus } = useQuery({
    queryKey: ["system", "config-status"],
    queryFn: getConfigStatus,
    retry: false,
  });

  const { data: auditLogs } = useQuery({
    queryKey: ["system", "audit"],
    queryFn: getAuditLogs,
    retry: false,
  });

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Settings</h1>
      </div>

      <div className="bg-white rounded-xl shadow p-6 max-w-xl mb-6">
        <h2 className="text-lg font-semibold mb-4">Account</h2>

        <div className="space-y-2 text-sm text-slate-600 mb-6">
          <div>
            <span className="font-medium text-slate-800">Username: </span>
            {user?.username}
          </div>
          <div>
            <span className="font-medium text-slate-800">Full name: </span>
            {user?.full_name}
          </div>
          <div>
            <span className="font-medium text-slate-800">Email: </span>
            {user?.email}
          </div>
        </div>

        <button
          onClick={logout}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
        >
          Sign Out
        </button>
      </div>

      {configStatus && (
        <div className="bg-white rounded-xl shadow p-6 max-w-3xl mb-6">
          <h2 className="text-lg font-semibold mb-1">Notification Channel Status</h2>
          <p className="text-xs text-gray-400 mb-4">
            Provider credentials are configured in the backend's <code>.env</code> file, not
            here -- this is a read-only status view. Update <code>.env</code> and restart the
            backend to change any of these.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">Email (SMTP)</span>
                <StatusPill ok={configStatus.email.configured} label={configStatus.email.configured ? "Configured" : "Not configured"} />
              </div>
              {configStatus.email.configured && (
                <p className="text-xs text-gray-500">
                  {configStatus.email.host} - {configStatus.email.username}
                </p>
              )}
            </div>

            <div className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">WhatsApp ({configStatus.whatsapp.provider})</span>
                <StatusPill ok={configStatus.whatsapp.configured} label={configStatus.whatsapp.configured ? "Configured" : "Not configured"} />
              </div>
              {configStatus.whatsapp.business_number && (
                <p className="text-xs text-gray-500">{configStatus.whatsapp.business_number}</p>
              )}
            </div>

            <div className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">SMS (Twilio)</span>
                <StatusPill ok={configStatus.sms.configured} label={configStatus.sms.configured ? "Configured" : "Not configured"} />
              </div>
              {configStatus.sms.from_number && (
                <p className="text-xs text-gray-500">{configStatus.sms.from_number}</p>
              )}
            </div>

            <div className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">Background Scheduler</span>
                <StatusPill ok={configStatus.scheduler.enabled} label={configStatus.scheduler.enabled ? "Running" : "Disabled"} />
              </div>
              <p className="text-xs text-gray-500">
                Offline threshold: {configStatus.scheduler.offline_threshold_minutes} min
              </p>
            </div>

            <div className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">Admin Alert Emails</span>
                <StatusPill ok={configStatus.admin_alerts.configured} label={`${configStatus.admin_alerts.recipient_count} recipient(s)`} />
              </div>
              <p className="text-xs text-gray-500">Used for DB-down / system alerts.</p>
            </div>

            <div className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">System Webhook Token</span>
                <StatusPill ok={configStatus.system_webhook.token_set} label={configStatus.system_webhook.token_set ? "Set" : "Open (no token)"} />
              </div>
              <p className="text-xs text-gray-500">
                Protects POST /system/report-failure for external scripts.
              </p>
            </div>
          </div>
        </div>
      )}

      {auditLogs && (
        <div className="bg-white rounded-xl shadow p-6 max-w-4xl">
          <h2 className="text-lg font-semibold mb-4">Audit Log</h2>
          {auditLogs.length === 0 ? (
            <p className="text-sm text-gray-400">No audit entries yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-200">
                  <th className="py-2 pr-4">Action</th>
                  <th className="py-2 pr-4">Target</th>
                  <th className="py-2 pr-4">Detail</th>
                  <th className="py-2 pr-4">When</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-100">
                    <td className="py-2 pr-4 font-mono text-xs">{log.action}</td>
                    <td className="py-2 pr-4">{log.target ?? "-"}</td>
                    <td className="py-2 pr-4">{log.detail ?? "-"}</td>
                    <td className="py-2 pr-4">{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </Layout>
  );
}
