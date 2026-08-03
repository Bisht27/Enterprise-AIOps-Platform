import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { RotateCw, Send } from "lucide-react";

import {
  getPreferences,
  updatePreferences,
  getDeliveryHistory,
  retryDelivery,
  sendTestEmail,
  sendTestWhatsApp,
  sendTestSlack,
  sendTestTeams,
  sendTestSms,
  type NotificationPreferences,
} from "../services/notification";

const CHANNEL_TOGGLES: { key: keyof NotificationPreferences; label: string }[] = [
  { key: "in_app_enabled", label: "In-App Notifications" },
  { key: "email_enabled", label: "Email Notifications" },
  { key: "whatsapp_enabled", label: "WhatsApp Notifications" },
  { key: "slack_enabled", label: "Slack Notifications" },
  { key: "teams_enabled", label: "Microsoft Teams Notifications" },
  { key: "sms_enabled", label: "SMS Notifications" },
];

const CATEGORY_TOGGLES: { key: keyof NotificationPreferences; label: string }[] = [
  { key: "critical_alerts", label: "Critical Alerts" },
  { key: "warning_alerts", label: "Warning Alerts" },
  { key: "offline_alerts", label: "Offline / Online Alerts" },
  { key: "ticket_notifications", label: "Ticket Notifications" },
  { key: "maintenance_alerts", label: "Maintenance Alerts" },
  { key: "security_alerts", label: "Security Alerts" },
  { key: "daily_summary", label: "Daily Summary" },
  { key: "weekly_summary", label: "Weekly Summary" },
];

const STATUS_COLORS: Record<string, string> = {
  Sent: "bg-green-100 text-green-700",
  Delivered: "bg-green-100 text-green-700",
  Pending: "bg-gray-100 text-gray-600",
  Retrying: "bg-amber-100 text-amber-700",
  Failed: "bg-red-100 text-red-700",
};

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
        checked ? "bg-blue-600" : "bg-gray-300"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

export default function Notifications() {
  const queryClient = useQueryClient();
  const [testEmail, setTestEmail] = useState("");
  const [testNumber, setTestNumber] = useState("");
  const [testSlackUrl, setTestSlackUrl] = useState("");
  const [testTeamsUrl, setTestTeamsUrl] = useState("");
  const [testSmsNumber, setTestSmsNumber] = useState("");

  const { data: preferences } = useQuery({
    queryKey: ["notifications", "preferences"],
    queryFn: getPreferences,
  });

  const { data: history = [] } = useQuery({
    queryKey: ["notifications", "history"],
    queryFn: getDeliveryHistory,
  });

  const updateMutation = useMutation({
    mutationFn: updatePreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(["notifications", "preferences"], data);
    },
    onError: () => toast.error("Could not update preferences"),
  });

  const retryMutation = useMutation({
    mutationFn: retryDelivery,
    onSuccess: () => {
      toast.success("Retry attempted");
      queryClient.invalidateQueries({ queryKey: ["notifications", "history"] });
    },
    onError: () => toast.error("Retry failed"),
  });

  const handleToggle = (key: keyof NotificationPreferences, value: boolean) => {
    updateMutation.mutate({ [key]: value });
  };

  const handleTestEmail = async () => {
    if (!testEmail) return toast.error("Enter an email address first");
    try {
      await sendTestEmail(testEmail);
      toast.success("Test email sent");
    } catch {
      toast.error("Test email failed - check SMTP settings");
    }
  };

  const handleTestWhatsApp = async () => {
    if (!testNumber) return toast.error("Enter a phone number first");
    try {
      await sendTestWhatsApp(testNumber);
      toast.success("Test WhatsApp message sent");
    } catch {
      toast.error("Test WhatsApp failed - check provider settings");
    }
  };

  const handleTestSlack = async () => {
    if (!testSlackUrl) return toast.error("Enter a Slack webhook URL first");
    try {
      await sendTestSlack(testSlackUrl);
      toast.success("Test Slack message sent");
    } catch {
      toast.error("Test Slack failed - check the webhook URL");
    }
  };

  const handleTestTeams = async () => {
    if (!testTeamsUrl) return toast.error("Enter a Teams webhook URL first");
    try {
      await sendTestTeams(testTeamsUrl);
      toast.success("Test Teams message sent");
    } catch {
      toast.error("Test Teams failed - check the webhook URL");
    }
  };

  const handleTestSms = async () => {
    if (!testSmsNumber) return toast.error("Enter a phone number first");
    try {
      await sendTestSms(testSmsNumber);
      toast.success("Test SMS sent");
    } catch {
      toast.error("Test SMS failed - check Twilio settings");
    }
  };

  if (!preferences) {
    return <div className="p-6 text-gray-500">Loading preferences...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Notification Preferences</h1>

      {/* Channels */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Channels</h2>
        <div className="space-y-4">
          {CHANNEL_TOGGLES.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-gray-700">{label}</span>
              <Toggle
                checked={Boolean(preferences[key])}
                onChange={(value) => handleToggle(key, value)}
              />
            </div>
          ))}

          {preferences.whatsapp_enabled && (
            <div className="pt-2">
              <label className="text-sm text-gray-600 block mb-1">
                WhatsApp Number
              </label>
              <input
                type="text"
                defaultValue={preferences.whatsapp_number ?? ""}
                placeholder="+15551234567"
                onBlur={(e) =>
                  updateMutation.mutate({ whatsapp_number: e.target.value })
                }
                className="border border-gray-300 rounded-md px-3 py-2 text-sm w-64"
              />
            </div>
          )}

          {preferences.slack_enabled && (
            <div className="pt-2">
              <label className="text-sm text-gray-600 block mb-1">
                Slack Incoming Webhook URL
              </label>
              <input
                type="text"
                defaultValue={preferences.slack_webhook_url ?? ""}
                placeholder="https://hooks.slack.com/services/..."
                onBlur={(e) =>
                  updateMutation.mutate({ slack_webhook_url: e.target.value })
                }
                className="border border-gray-300 rounded-md px-3 py-2 text-sm w-96"
              />
            </div>
          )}

          {preferences.teams_enabled && (
            <div className="pt-2">
              <label className="text-sm text-gray-600 block mb-1">
                Microsoft Teams Webhook URL
              </label>
              <input
                type="text"
                defaultValue={preferences.teams_webhook_url ?? ""}
                placeholder="https://outlook.office.com/webhook/..."
                onBlur={(e) =>
                  updateMutation.mutate({ teams_webhook_url: e.target.value })
                }
                className="border border-gray-300 rounded-md px-3 py-2 text-sm w-96"
              />
            </div>
          )}

          {preferences.sms_enabled && (
            <div className="pt-2">
              <label className="text-sm text-gray-600 block mb-1">
                SMS Phone Number
              </label>
              <input
                type="text"
                defaultValue={preferences.sms_number ?? ""}
                placeholder="+15551234567"
                onBlur={(e) =>
                  updateMutation.mutate({ sms_number: e.target.value })
                }
                className="border border-gray-300 rounded-md px-3 py-2 text-sm w-64"
              />
            </div>
          )}
        </div>
      </div>

      {/* Categories */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Event Categories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {CATEGORY_TOGGLES.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-gray-700">{label}</span>
              <Toggle
                checked={Boolean(preferences[key])}
                onChange={(value) => handleToggle(key, value)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Test notifications */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Test Notifications</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="flex gap-2">
            <input
              type="email"
              placeholder="test@company.com"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
            />
            <button
              onClick={handleTestEmail}
              className="flex items-center gap-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 whitespace-nowrap"
            >
              <Send size={14} /> Email
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="+15551234567"
              value={testNumber}
              onChange={(e) => setTestNumber(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
            />
            <button
              onClick={handleTestWhatsApp}
              className="flex items-center gap-1 bg-green-600 text-white px-4 py-2 rounded-md text-sm hover:bg-green-700 whitespace-nowrap"
            >
              <Send size={14} /> WhatsApp
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Slack webhook URL"
              value={testSlackUrl}
              onChange={(e) => setTestSlackUrl(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
            />
            <button
              onClick={handleTestSlack}
              className="flex items-center gap-1 bg-purple-600 text-white px-4 py-2 rounded-md text-sm hover:bg-purple-700 whitespace-nowrap"
            >
              <Send size={14} /> Slack
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Teams webhook URL"
              value={testTeamsUrl}
              onChange={(e) => setTestTeamsUrl(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
            />
            <button
              onClick={handleTestTeams}
              className="flex items-center gap-1 bg-indigo-600 text-white px-4 py-2 rounded-md text-sm hover:bg-indigo-700 whitespace-nowrap"
            >
              <Send size={14} /> Teams
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="+15551234567"
              value={testSmsNumber}
              onChange={(e) => setTestSmsNumber(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
            />
            <button
              onClick={handleTestSms}
              className="flex items-center gap-1 bg-orange-600 text-white px-4 py-2 rounded-md text-sm hover:bg-orange-700 whitespace-nowrap"
            >
              <Send size={14} /> SMS
            </button>
          </div>
        </div>
      </div>

      {/* Delivery history */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Delivery History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-2 pr-4">Channel</th>
                <th className="py-2 pr-4">Recipient</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Provider</th>
                <th className="py-2 pr-4">Retries</th>
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-gray-400">
                    No delivery history yet
                  </td>
                </tr>
              )}
              {history.map((d) => (
                <tr key={d.id} className="border-b border-gray-100">
                  <td className="py-2 pr-4 capitalize">{d.channel}</td>
                  <td className="py-2 pr-4">{d.recipient}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_COLORS[d.status] || "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {d.status}
                    </span>
                  </td>
                  <td className="py-2 pr-4">{d.provider ?? "-"}</td>
                  <td className="py-2 pr-4">{d.retry_count}</td>
                  <td className="py-2 pr-4">
                    {new Date(d.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4">
                    {d.status === "Failed" && (
                      <button
                        onClick={() => retryMutation.mutate(d.id)}
                        className="flex items-center gap-1 text-blue-600 hover:underline text-xs"
                      >
                        <RotateCw size={12} /> Retry
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
