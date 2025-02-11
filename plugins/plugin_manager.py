from pathlib import Path
import importlib.util
import logging
from typing import Dict, List, Type
from .base_plugin import AlarmPlugin

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, plugins_dir: Path):
        """Initialize the plugin manager.

        Args:
            plugins_dir: Path to the plugins directory
        """
        logger.debug("Initializing plugin manager with directory: %s", plugins_dir)
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, AlarmPlugin] = {}

    def discover_plugins(self) -> None:
        """Discover and load all plugins in the plugins directory."""
        logger.info("Starting plugin discovery")
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                logger.debug(
                    "Skipping %s: not a valid plugin directory", plugin_dir.name
                )
                continue

            try:
                logger.debug("Examining potential plugin: %s", plugin_dir.name)
                # Look for plugin.py in the plugin directory
                plugin_file = plugin_dir / "plugin.py"
                if not plugin_file.exists():
                    logger.debug("No plugin.py found in %s", plugin_dir.name)
                    continue

                # Load the module
                spec = importlib.util.spec_from_file_location("plugins.%s", plugin_file)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find the plugin class (subclass of AlarmPlugin)
                plugin_class = None
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, AlarmPlugin)
                        and obj != AlarmPlugin
                    ):
                        plugin_class = obj
                        break

                logger.debug("Loading plugin module: %s", plugin_dir.name)

                if plugin_class is None:
                    logger.warning("No valid plugin class found in %s", plugin_dir.name)
                    continue

                # Initialize the plugin
                logger.debug("Initializing plugin: %s", plugin_dir.name)
                plugin = plugin_class(plugin_dir)
                if plugin.initialize():
                    self.plugins[plugin_dir.name] = plugin
                    logger.info("Successfully loaded plugin: %s", plugin_dir.name)
                else:
                    logger.error("Plugin initialization failed: %s", plugin_dir.name)

            except Exception as e:
                logger.error(
                    "Error loading plugin %s: %s", plugin_dir.name, e, exc_info=True
                )

    def execute_all(self, alarm_id: str, plugin_list: List[str] = None) -> None:
        """Execute all plugins or specified plugins for an alarm.

        Args:
            alarm_id: Unique identifier for the alarm
            plugin_list: Optional list of plugin names to execute
        """
        logger.debug("Executing plugins for alarm %s", alarm_id)
        if plugin_list:
            logger.debug("Using specific plugin list: %s", plugin_list)

        plugins_to_execute = self.plugins
        if plugin_list:
            plugins_to_execute = {
                name: plugin
                for name, plugin in self.plugins.items()
                if name in plugin_list
            }

        for name, plugin in plugins_to_execute.items():
            try:
                logger.info("Executing plugin %s for alarm %s", name, alarm_id)
                plugin.execute(alarm_id)
                logger.debug("Plugin %s execution completed", name)
            except Exception as e:
                logger.error("Error executing plugin %s: %s", name, e, exc_info=True)

    def cleanup(self) -> None:
        """Cleanup all plugins."""
        for name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error("Error cleaning up plugin %s: %s", name, e)
