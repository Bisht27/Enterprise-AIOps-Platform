"""
Demo / test agent.

Simulates ONE additional monitored system using the exact same
registration + heartbeat calls as the real agent -- collector.py,
sender.py, identity.py, and config.py are reused completely unchanged.
The only thing this script does differently is relabel the payload
with a fake hostname + MAC address + its own UUID, so each instance
registers as its own separate asset instead of colliding with your
real machine's row (the backend matches returning agents by
agent_uuid first, then falls back to MAC address -- so both need to
be different, not just the UUID).

Drop this file into the same AIOpa-agent/ folder as collector.py,
sender.py, identity.py, and config.py.

Usage (run each in its own terminal):
    python demo_agent.py --name "Demo-Server-01"
    python demo_agent.py --name "Demo-Server-02"
    python demo_agent.py --name "Office-PC-Test"

Run as many of these as the number of fake systems you want visible
on the Dashboard. Each --name gets its own local identity cache file
(agent_identity_<name>.json), so re-running with the same --name
always updates that same simulated asset instead of creating a new
one every time you restart it.

Real hardware/OS metrics (CPU, RAM, Disk, etc.) still come from this
actual machine via collector.py -- only the identity fields are
faked. A small random jitter is added to CPU/RAM so simulated systems
don't show numbers identical to your real agent on every chart.
"""

import argparse
import hashlib
import os
import random
import time
import uuid

import identity
from collector import get_system_info, get_live_metrics
from sender import register_agent, send_metrics
from config import HEARTBEAT_INTERVAL


def fake_mac(name: str) -> str:
    """
    Deterministic, clearly-fake MAC derived from --name so the same
    --name always produces the same MAC across restarts (needed for
    the backend to recognize it as the same asset), while different
    --name values never collide with each other or with a real NIC.

    Starts with 02: (the "locally administered, unicast" bit pattern),
    which real hardware vendors never use, so it can never accidentally
    match a genuine MAC address.
    """
    digest = hashlib.md5(name.encode()).hexdigest()
    return "02:" + ":".join(digest[i:i + 2] for i in range(0, 10, 2)).upper()


def main():
    parser = argparse.ArgumentParser(
        description="Simulate an additional monitored system for frontend testing."
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Display name for this simulated system, e.g. 'Demo-Server-01'",
    )
    args = parser.parse_args()

    # Give this simulated agent its own identity cache file, isolated
    # from the real agent's agent_identity.json (and from any other
    # --name), by pointing identity.py's IDENTITY_FILE at a new path
    # before calling any of its functions.
    safe_name = "".join(c if c.isalnum() else "_" for c in args.name)
    identity.IDENTITY_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"agent_identity_{safe_name}.json",
    )

    print("=" * 50)
    print(f"Starting Simulated Agent: {args.name}")
    print("=" * 50)

    cached = identity.load_identity()
    if cached:
        agent_uuid = cached["agent_uuid"]
        print(f"Using cached identity: {agent_uuid}")
    else:
        agent_uuid = str(uuid.uuid4())

    mac = fake_mac(args.name)
    asset_id = None

    while asset_id is None:
        try:
            # Real hardware/OS info collected from this machine (same
            # collector.py as the real agent), just relabeled below.
            system_info = get_system_info()
            system_info["hostname"] = args.name
            system_info["mac_address"] = mac
            system_info["agent_uuid"] = agent_uuid

            asset_id = register_agent(system_info)

            if asset_id is None:
                print("Registration failed. Retrying in 10s...")
                time.sleep(10)

        except KeyboardInterrupt:
            print("\nStopped before registration.")
            return

    print(f"Registered as Asset ID {asset_id} ({args.name})")
    print("=" * 50)

    while True:
        try:
            metrics = get_live_metrics()
            metrics["asset_id"] = asset_id

            # Jitter so this simulated system doesn't mirror the real
            # agent's numbers exactly on every heartbeat.
            metrics["cpu_usage"] = max(
                0, min(100, metrics["cpu_usage"] + random.uniform(-8, 8))
            )
            metrics["ram_usage"] = max(
                0, min(100, metrics["ram_usage"] + random.uniform(-5, 5))
            )

            print(f"\n[{args.name}] Sending metrics...")
            print(metrics)

            send_metrics(metrics)

            print("Waiting for next heartbeat...\n")
            time.sleep(HEARTBEAT_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n{args.name} stopped by user.")
            break

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()