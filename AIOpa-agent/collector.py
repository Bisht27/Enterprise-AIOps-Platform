import platform
import socket
import subprocess
import uuid

import psutil


# ==========================================================
# Best-effort helpers
# ==========================================================
# Motherboard / BIOS / GPU / serial number detection needs different
# OS-specific tooling and is not always available (missing tool, no
# permissions, virtualized hardware). Every helper here returns None on
# failure instead of raising, so a missing detail never blocks
# registration -- the backend/UI show "Not available" for it.

def _run(cmd, timeout=3):
    try:
        output = subprocess.check_output(
            cmd, timeout=timeout, stderr=subprocess.DEVNULL
        )
        return output.decode(errors="ignore").strip()
    except Exception:
        return None


def get_serial_number():
    system = platform.system()

    if system == "Windows":
        out = _run(["wmic", "bios", "get", "serialnumber"])
        if out:
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if len(lines) >= 2:
                return lines[1]
        return None

    if system == "Linux":
        try:
            with open("/sys/class/dmi/id/product_serial") as f:
                value = f.read().strip()
                return value or None
        except Exception:
            return None

    return None


def get_motherboard():
    system = platform.system()

    if system == "Windows":
        out = _run(["wmic", "baseboard", "get", "product"])
        if out:
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if len(lines) >= 2:
                return lines[1]
        return None

    if system == "Linux":
        try:
            with open("/sys/class/dmi/id/board_name") as f:
                value = f.read().strip()
                return value or None
        except Exception:
            return None

    return None


def get_bios_version():
    system = platform.system()

    if system == "Windows":
        out = _run(["wmic", "bios", "get", "smbiosbiosversion"])
        if out:
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if len(lines) >= 2:
                return lines[1]
        return None

    if system == "Linux":
        try:
            with open("/sys/class/dmi/id/bios_version") as f:
                value = f.read().strip()
                return value or None
        except Exception:
            return None

    return None


def get_gpu():
    system = platform.system()

    if system == "Windows":
        out = _run(["wmic", "path", "win32_VideoController", "get", "name"])
        if out:
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if len(lines) >= 2:
                return ", ".join(lines[1:])
        return None

    if system == "Linux":
        out = _run(["lspci"])
        if out:
            gpu_lines = [
                line.split(": ", 1)[-1]
                for line in out.splitlines()
                if "VGA" in line or "3D controller" in line
            ]
            if gpu_lines:
                return ", ".join(gpu_lines)
        return None

    return None


def get_cloud_info():
    """
    Best-effort cloud metadata probe (AWS/Azure/GCP). Uses a very short
    timeout so this is near-instant on non-cloud machines (no
    169.254.169.254 route -> fails fast). Returns
    (provider, region, instance_id), all None if not detected.
    """
    try:
        import requests
    except ImportError:
        return None, None, None

    # AWS (IMDSv1 -- good enough for a best-effort probe)
    try:
        r = requests.get(
            "http://169.254.169.254/latest/dynamic/instance-identity/document",
            timeout=0.3,
        )
        if r.status_code == 200:
            data = r.json()
            return "AWS", data.get("region"), data.get("instanceId")
    except Exception:
        pass

    # Azure
    try:
        r = requests.get(
            "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
            headers={"Metadata": "true"},
            timeout=0.3,
        )
        if r.status_code == 200:
            data = r.json().get("compute", {})
            return "Azure", data.get("location"), data.get("vmId")
    except Exception:
        pass

    # GCP
    try:
        r = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/zone",
            headers={"Metadata-Flavor": "Google"},
            timeout=0.3,
        )
        if r.status_code == 200:
            zone = r.text.rsplit("/", 1)[-1]
            id_resp = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/id",
                headers={"Metadata-Flavor": "Google"},
                timeout=0.3,
            )
            instance_id = id_resp.text if id_resp.status_code == 200 else None
            return "GCP", zone, instance_id
    except Exception:
        pass

    return None, None, None


# ==========================================================
# System Info (sent once at registration)
# ==========================================================

def get_system_info():

    disk = psutil.disk_usage("/")

    cloud_provider, cloud_region, instance_id = get_cloud_info()

    return {
        "hostname": socket.gethostname(),

        "private_ip": socket.gethostbyname(socket.gethostname()),

        "public_ip": None,

        "mac_address": ":".join(
            ("%012X" % uuid.getnode())[i:i + 2]
            for i in range(0, 12, 2)
        ),

        "os_name": platform.platform(),
        "os_version": platform.version(),

        "cpu_name": platform.processor(),

        "cpu_cores": psutil.cpu_count(logical=False),

        "cpu_threads": psutil.cpu_count(),

        "ram_total": str(round(
            psutil.virtual_memory().total / (1024 ** 3),
            2,
        )),

        "disk_total": str(round(
            disk.total / (1024 ** 3),
            2,
        )),

        "disk_used": str(round(
            disk.used / (1024 ** 3),
            2,
        )),

        "disk_free": str(round(
            disk.free / (1024 ** 3),
            2,
        )),

        "serial_number": get_serial_number(),
        "motherboard": get_motherboard(),
        "bios_version": get_bios_version(),
        "gpu": get_gpu(),

        "cloud_provider": cloud_provider,
        "cloud_region": cloud_region,
        "instance_id": instance_id,

        "agent_version": "1.0.0",
    }


def get_logged_in_user():
    """
    Best-effort -- returns None (shown as "N/A" downstream) rather than
    raising, since headless/service accounts and some sandboxed
    environments won't have a console session at all.
    """
    try:
        users = psutil.users()
        if users:
            return ", ".join(sorted({u.name for u in users}))
    except Exception:
        pass
    return None


def get_running_processes_count():
    try:
        return len(psutil.pids())
    except Exception:
        return None


def get_live_metrics():

    disk = psutil.disk_usage("/")

    network = psutil.net_io_counters()

    return {

        "cpu_usage": psutil.cpu_percent(interval=1),

        "ram_usage": psutil.virtual_memory().percent,

        "disk_usage": disk.percent,

        "network_sent": network.bytes_sent,

        "network_received": network.bytes_recv,

        "logged_in_user": get_logged_in_user(),

        "running_processes": get_running_processes_count(),
    }
