import json
import os

from config import IDENTITY_FILE


def load_identity():
    """Return {"agent_uuid": ..., "api_key": ...} from a previous
    registration, or None if this agent has never registered before."""
    if not os.path.exists(IDENTITY_FILE):
        return None

    try:
        with open(IDENTITY_FILE, "r") as f:
            data = json.load(f)
            if data.get("agent_uuid") and data.get("api_key"):
                return data
    except Exception:
        pass

    return None


def save_identity(agent_uuid, api_key):
    try:
        with open(IDENTITY_FILE, "w") as f:
            json.dump({"agent_uuid": agent_uuid, "api_key": api_key}, f)
    except Exception as e:
        print(f"Warning: could not cache agent identity locally: {e}")
