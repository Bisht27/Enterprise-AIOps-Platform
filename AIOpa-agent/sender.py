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
            timeout=15,
        )

        if response.status_code != 200:
            print(f"Registration Failed ({response.status_code})")
            print(response.text)
            return None

        result = response.json()

        print("=" * 60)
        print("Agent Registered Successfully")
        print(f"Asset ID   : {result['asset_id']}")
        print(f"Hostname   : {result['hostname']}")
        print(f"Agent UUID : {result.get('agent_uuid')}")
        print("=" * 60)

        # Save identity for future heartbeats
        if result.get("agent_uuid") and result.get("api_key"):
            save_identity(
                result["agent_uuid"],
                result["api_key"],
            )

        return result["asset_id"]

    except requests.exceptions.RequestException as e:
        print(f"Registration Error: {e}")
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

        print("Heartbeat Sent")

    except requests.exceptions.RequestException as e:
        print(f"Monitoring Error: {e}")