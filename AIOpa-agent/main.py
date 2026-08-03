import time

from collector import (
    get_system_info,
    get_live_metrics,
)

from sender import (
    register_agent,
    send_metrics,
)

from identity import load_identity

from config import HEARTBEAT_INTERVAL


def main():
    print("=" * 50)
    print("Starting AIOps Monitoring Agent")
    print("=" * 50)

    # Register agent with backend
    system_info = get_system_info()

    # If this agent has registered before, send its cached agent_uuid so
    # the backend recognizes it as the same asset (matches even if its
    # MAC address changed, e.g. a VM moved to a different NIC).
    cached_identity = load_identity()
    if cached_identity:
        system_info["agent_uuid"] = cached_identity["agent_uuid"]
        print(f"Using cached agent identity: {cached_identity['agent_uuid']}")

    asset_id = register_agent(system_info)

    if asset_id is None:
        print("❌ Failed to register agent.")
        return

    print(f"✅ Agent Registered Successfully")
    print(f"📌 Asset ID: {asset_id}")
    print("=" * 50)

    # Start heartbeat loop
    while True:
        try:
            metrics = get_live_metrics()

            # Attach asset_id so backend knows which server sent the metrics
            metrics["asset_id"] = asset_id

            print("\nSending Metrics...")
            print(metrics)

            send_metrics(metrics)

            print("Waiting for next heartbeat...\n")

            time.sleep(HEARTBEAT_INTERVAL)

        except KeyboardInterrupt:
            print("\nAgent stopped by user.")
            break

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
