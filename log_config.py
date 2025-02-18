import logging
from config_manager import JsonConfig
from typing import Optional
import urllib3


def setup_logging(config_file: str = "ulticlock.config") -> None:
    """Set up logging configuration for the entire application.

    Args:
        config_file: Path to the config file containing debug_level setting
    """
    config = JsonConfig(config_file)
    logging_level = getattr(logging, config.debug_level.upper(), logging.INFO)

    # Clear any existing handlers to avoid duplicate logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Disable urllib3's default stderr logger
    urllib3.disable_warnings()

    # Configure root logger
    logging.basicConfig(
        level=logging_level, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )

    # Get root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging_level)

    # Configure urllib3 logging
    urllib3_logger = logging.getLogger("urllib3")
    if logging_level > logging.DEBUG:
        urllib3_logger.setLevel(logging.WARNING)
    else:
        # For debug level, we still want to use our format
        urllib3_logger.setLevel(logging.DEBUG)
        # Remove any existing handlers
        for handler in urllib3_logger.handlers[:]:
            urllib3_logger.removeHandler(handler)

    logger = logging.getLogger(__name__)
    logger.debug("Logging configured with level %s", config.debug_level)
