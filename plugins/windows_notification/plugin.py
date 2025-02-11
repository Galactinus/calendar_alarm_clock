from plugins.base_plugin import AlarmPlugin
from typing import Dict, Any, Optional
from notification_server.client import NotificationClient
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WindowsNotificationPlugin(AlarmPlugin):
    def initialize(self) -> bool:
        logger.debug("Initializing Windows notification plugin")
        try:
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 5000)
            logger.debug("Configuring client with host=%s, port=%s", host, port)
            self.client = NotificationClient(host=host, port=port)
            logger.info("Windows notification plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(
                "Failed to initialize Windows notification plugin: %s",
                e,
                exc_info=True
            )
            return False
    
    def execute(self, alarm_id: str, context: Optional[Dict[str, Any]] = None) -> bool:
        logger.debug("Executing notification for alarm %s", alarm_id)
        try:
            message = f"Alarm triggered: {alarm_id}"
            if context and 'message' in context:
                message = context['message']
            logger.debug("Sending notification: %s", message)
            result = self.client.send_notification(message)
            if result:
                logger.info("Successfully sent notification for alarm %s", alarm_id)
            else:
                logger.warning("Failed to send notification for alarm %s", alarm_id)
            return result
        except Exception as e:
            logger.error("Failed to send notification: %s", e, exc_info=True)
            return False
    
    def cleanup(self) -> None:
        """Clean up resources."""
        pass 