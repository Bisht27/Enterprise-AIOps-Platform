"""
Catalog of every event the Enterprise Notification Service knows how
to send. Adding a new event = adding one line here (plus, usually, one
call to `notification_service.notify(...)` at the point the event
happens -- see app/services/notification_service.py docstring).

`category` maps an event to the matching NotificationPreference
column, so a user's toggle actually controls delivery.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventDefinition:
    event_type: str
    label: str
    default_severity: str  # Critical | Warning | Info
    category: str  # matches a NotificationPreference boolean column


EVENTS: dict[str, EventDefinition] = {
    d.event_type: d
    for d in [
        EventDefinition("critical_cpu_alert", "Critical CPU Alert", "Critical", "critical_alerts"),
        EventDefinition("critical_ram_alert", "Critical RAM Alert", "Critical", "critical_alerts"),
        EventDefinition("critical_disk_alert", "Critical Disk Alert", "Critical", "critical_alerts"),
        EventDefinition("monitoring_alert", "Enterprise AIOps Alert", "Warning", "critical_alerts"),
        EventDefinition("monitoring_recovery", "Enterprise AIOps Alert Recovered", "Info", "critical_alerts"),
        EventDefinition("server_offline", "Server Offline", "Critical", "offline_alerts"),
        EventDefinition("server_online", "Server Online Again", "Info", "offline_alerts"),
        EventDefinition("agent_registered", "Agent Registered", "Info", "ticket_notifications"),
        EventDefinition("asset_added", "New Asset Added", "Info", "ticket_notifications"),
        EventDefinition("asset_deleted", "Asset Deleted", "Warning", "ticket_notifications"),
        EventDefinition("asset_updated", "Asset Updated", "Info", "ticket_notifications"),
        EventDefinition("ticket_created", "Ticket Created", "Info", "ticket_notifications"),
        EventDefinition("ticket_assigned", "Ticket Assigned", "Info", "ticket_notifications"),
        EventDefinition("ticket_closed", "Ticket Closed", "Info", "ticket_notifications"),
        EventDefinition("ticket_escalated", "Ticket Escalated", "Warning", "ticket_notifications"),
        EventDefinition("warranty_expiry_reminder", "Warranty Expiry Reminder", "Warning", "maintenance_alerts"),
        EventDefinition("license_expiry_reminder", "License Expiry Reminder", "Warning", "maintenance_alerts"),
        EventDefinition("maintenance_reminder", "Maintenance Reminder", "Info", "maintenance_alerts"),
        EventDefinition("security_incident", "Security Incident", "Critical", "security_alerts"),
        EventDefinition("login_new_device", "Login from New Device", "Warning", "security_alerts"),
        EventDefinition("failed_login_attempts", "Failed Login Attempts", "Warning", "security_alerts"),
        EventDefinition("backup_failed", "Backup Failed", "Critical", "critical_alerts"),
        EventDefinition("database_down", "Database Down", "Critical", "critical_alerts"),
        EventDefinition("application_down", "Application Down", "Critical", "critical_alerts"),
        EventDefinition("high_memory_usage", "High Memory Usage", "Warning", "warning_alerts"),
        EventDefinition("high_network_usage", "High Network Usage", "Warning", "warning_alerts"),
        EventDefinition("high_disk_usage", "High Disk Usage", "Warning", "warning_alerts"),
        EventDefinition("health_status_changed", "Health Status Changed", "Info", "warning_alerts"),
    ]
}


def get_event(event_type: str) -> EventDefinition:
    return EVENTS.get(
        event_type,
        EventDefinition(event_type, event_type.replace("_", " ").title(), "Info", "warning_alerts"),
    )
