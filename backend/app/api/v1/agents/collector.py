import platform
import socket
import time
import uuid

import cpuinfo
import psutil
import requests


def get_private_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return None


def get_public_ip():
    try:
        return requests.get(
            "https://api.ipify.org",
            timeout=5,
        ).text
    except Exception:
        return None


def collect():

    cpu = cpuinfo.get_cpu_info()

    ram = psutil.virtual_memory()

    disk = psutil.disk_usage("/")

    network = psutil.net_io_counters()

    boot_time = psutil.boot_time()

    uptime = time.time() - boot_time

    return {

        # Asset Information
        "hostname": socket.gethostname(),

        "cpu_name": cpu.get("brand_raw"),

        "cpu_cores": psutil.cpu_count(logical=False),

        "cpu_threads": psutil.cpu_count(logical=True),

        "ram_total": f"{round(ram.total/1024**3,2)} GB",

        "disk_total": f"{round(disk.total/1024**3,2)} GB",

        "disk_used": f"{round(disk.used/1024**3,2)} GB",

        "disk_free": f"{round(disk.free/1024**3,2)} GB",

        "os_name": platform.platform(),

        "mac_address": ":".join(
            ("%012X" % uuid.getnode())[i:i+2]
            for i in range(0, 12, 2)
        ),

        "private_ip": get_private_ip(),

        "public_ip": get_public_ip(),

        "agent_version": "1.0.0",

        # Live Monitoring
        "cpu_usage": psutil.cpu_percent(interval=1),

        "ram_usage": ram.percent,

        "disk_usage": disk.percent,

        "network_sent": round(network.bytes_sent / 1024 / 1024, 2),

        "network_received": round(network.bytes_recv / 1024 / 1024, 2),

        "uptime": round(uptime, 2),
    }