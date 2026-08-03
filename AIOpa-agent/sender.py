import requests

from config import BACKEND_URL
from identity import save_identity


# ==========================================================
# Register Agent
# ==========================================================

def register_agent(data):
    try:
        response = requests.post(
            f"{BACKEND_URL}/agents/register",
            json=data,
            timeout=10,
        )

        if response.status_code != 200:
            print("Status Code:", response.status_code)
            print("Response:", response.text)
            return None

        result = response.json()

        print("===================================")
        print("Agent Registered Successfully")
        print(f"Asset ID : {result['asset_id']}")
        print(f"Hostname : {result['hostname']}")
        print("===================================")

        # Cache the identity the backend assigned so the next run of this
        # agent updates the same asset instead of creating a new one.
        if result.get("agent_uuid") and result.get("api_key"):
            save_identity(result["agent_uuid"], result["api_key"])

        # Return Asset ID
        return result["asset_id"]

    except Exception as e:
        print("Registration Error:", e)
        return None


# ==========================================================
# Send Monitoring Data
# ==========================================================

def send_metrics(data):
    try:
        response = requests.post(
            f"{BACKEND_URL}/monitoring/heartbeat",
            json=data,
            timeout=10,
        )

        response.raise_for_status()

        print("Metrics Sent Successfully")

    except Exception as e:
        print("Monitoring Error:", e)
