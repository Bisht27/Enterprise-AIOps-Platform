import json
import os
import platform
import hashlib

from config import IDENTITY_FILE


def get_machine_fingerprint():
    """
    Create a stable fingerprint for this machine.
    You can later improve this using BIOS serial,
    motherboard serial, CPU ID, etc.
    """
    data = "|".join([
        platform.node(),
        platform.machine(),
        platform.processor(),
    ])

    return hashlib.sha256(data.encode()).hexdigest()


def load_identity():
    if not os.path.exists(IDENTITY_FILE):
        return None

    try:
        with open(IDENTITY_FILE, "r") as f:
            data = json.load(f)

        if (
            data.get("agent_uuid")
            and data.get("api_key")
            and data.get("hardware_fingerprint")
        ):
            current_fp = get_machine_fingerprint()

            # Identity copied to another machine
            if current_fp != data["hardware_fingerprint"]:
                print("Machine changed. Creating new identity.")
                os.remove(IDENTITY_FILE)
                return None

            return data

    except Exception:
        pass

    return None


def save_identity(agent_uuid, api_key):
    try:
        identity = {
            "agent_uuid": agent_uuid,
            "api_key": api_key,
            "hardware_fingerprint": get_machine_fingerprint(),
        }

        with open(IDENTITY_FILE, "w") as f:
            json.dump(identity, f, indent=4)

    except Exception as e:
        print(f"Warning: {e}")