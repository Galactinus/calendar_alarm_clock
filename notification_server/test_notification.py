from client import NotificationClient
import time
import argparse


def test_notification(host="localhost"):
    print(f"Testing notification server at {host}...")

    # Create client
    client = NotificationClient(host=host)

    # Send test notification
    print("Sending test notification...")
    success = client.send_notification(
        "🔔 Test Notification: If you see this and hear a sound, the server is working!"
    )

    if success:
        print("✅ Notification sent successfully!")
    else:
        print("❌ Failed to send notification. Make sure the server is running.")
        print(f"   Start the server with: python server.py on {host}")


def test_multiple_notifications(host="localhost"):
    print(f"\nTesting multiple notifications to {host}...")

    client = NotificationClient(host=host)

    for i in range(3):
        message = f"🔔 Test Notification {i + 1}/3"
        print(f"Sending: {message}")
        success = client.send_notification(message)

        if success:
            print(f"✅ Notification {i + 1} sent successfully!")
        else:
            print(f"❌ Failed to send notification {i + 1}")

        # Wait a few seconds between notifications
        if i < 2:  # Don't wait after the last notification
            print("Waiting 3 seconds before next notification...")
            time.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the notification server")
    parser.add_argument(
        "--host",
        default="10.0.0.3",
        help="Notification server host (default: 10.0.0.3)",
    )
    args = parser.parse_args()

    print("=== Notification Server Test ===")
    print(f"Will connect to server at: {args.host}")
    print("Make sure the server is running before starting this test.")
    print("Press Enter to start the test...")
    input()

    test_notification(args.host)

    print("\nWould you like to test multiple notifications? (y/n)")
    if input().lower().startswith("y"):
        test_multiple_notifications(args.host)

    print("\nTests complete!")
