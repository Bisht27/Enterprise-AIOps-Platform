import os

BACKEND_URL = "http://127.0.0.1:8000/api/v1"

HEARTBEAT_INTERVAL = 30

# Where this agent caches its own identity (agent_uuid + api_key) once the
# backend has assigned them, so restarts reuse the same asset instead of
# creating a new one every time.
IDENTITY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "agent_identity.json"
)
