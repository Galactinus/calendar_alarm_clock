from abc import ABC, abstractmethod
from pathlib import Path
import json
from typing import Any, Dict, Optional

class AlarmPlugin(ABC):
    def __init__(self, plugin_dir: Path):
        """Initialize the plugin.
        
        Args:
            plugin_dir: Path to the plugin's directory
        """
        self.plugin_dir = plugin_dir
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load plugin configuration from config.json in plugin directory."""
        config_file = self.plugin_dir / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Called when plugin is loaded.
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    def execute(self, alarm_id: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Execute the plugin's alarm action.
        
        Args:
            alarm_id: Unique identifier for the alarm
            context: Optional context data for the alarm
            
        Returns:
            bool: True if execution successful
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources. Called when shutting down."""
        pass 