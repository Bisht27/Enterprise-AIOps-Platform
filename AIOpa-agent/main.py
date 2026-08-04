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
    print("=" * 60)
    print("Starting AIOps Monitoring Agent")
    print("=" * 60)

    # Collect hardware/system information
    system_info = get_system_info()

    # Load cached identity
    identity = load_identity()

    if identity:
        print(f"Using Agent UUID: {identity['agent_uuid']}")
        system_info["agent_uuid"] = identity["agent_uuid"]
    else:
        print("No cached identity found. Registering as a new agent.")
        system_info["agent_uuid"] = None

    # Register with backend
    asset_id = register_agent(system_info)

    if asset_id is None:
        print("\n❌ Registration failed.")
        return

    print("\n✅ Registration Successful")
    print(f"Asset ID : {asset_id}")
    print("=" * 60)

    while True:
        try:
            metrics = get_live_metrics()

            metrics["asset_id"] = asset_id

            print("\nSending Heartbeat...")
            send_metrics(metrics)

            print("Heartbeat sent successfully.")

            time.sleep(HEARTBEAT_INTERVAL)

        except KeyboardInterrupt:
            print("\nAgent stopped.")
            break

        except Exception as e:
            print(f"\nHeartbeat Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()