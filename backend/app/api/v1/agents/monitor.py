import time
import requests

from collector import collect

REGISTER_URL = "http://127.0.0.1:8000/api/v1/agents/register"
MONITORING_URL = "http://127.0.0.1:8000/api/v1/monitoring/"


while True:
    try:
        data = collect()

        register = requests.post(
            REGISTER_URL,
            json=data,
            timeout=10,
        )

        print("Register Status:", register.status_code)
        print("Register Response:", register.text)

        if register.status_code != 200:
            time.sleep(30)
            continue

        asset = register.json()

        monitoring = {
            "asset_id": asset["asset_id"],
            "cpu_usage": data["cpu_usage"],
            "ram_usage": data["ram_usage"],
            "disk_usage": data["disk_usage"],
            "network_sent": data["network_sent"],
            "network_received": data["network_received"],
            "uptime": data["uptime"],
        }

        response = requests.post(
            MONITORING_URL,
            json=monitoring,
            timeout=10,
        )

        print("Monitoring Status:", response.status_code)
        print("Monitoring Response:", response.text)

    except Exception as e:
        print("Error:", e)

    time.sleep(30)