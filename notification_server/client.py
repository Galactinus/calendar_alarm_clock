import requests
from typing import Optional

class NotificationClient:
    def __init__(self, host: str = "localhost", port: int = 5000):
        """Initialize the notification client.
        
        Args:
            host: Hostname of the notification server
            port: Port number of the notification server
        """
        self.base_url = f"http://{host}:{port}"
    
    def send_notification(self, message: str) -> bool:
        """Send a notification to the server.
        
        Args:
            message: The message to display in the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/notify",
                json={"message": message}
            )
            return response.status_code == 200
        except Exception:
            return False 