import json
from src.utils.datetime import get_formatted_datetime
from src.defaults import DEFAULT_AUTO_RESTART_ON_ERROR, DEFAULT_POST_GLOBAL_ERROR

class ErrorHandler:
    def __init__(self, config, power, lifecycle, mqtt_manager, logger):
        """
        Initialize the ErrorHandler.

        Args:
            lifecycle: Lifecycle manager for handling state transitions.
            mqtt_manager: MQTT manager for publishing errors.
            logger: Logger for logging errors and messages.
            power: Power manager for rebooting if needed.
            error_handling_config (dict): Configuration for error handling behavior.
            publish_cfg (dict): Configuration for publish topics.
        """
        self.lifecycle = lifecycle
        self.mqtt_manager = mqtt_manager
        self.logger = logger
        self.power = power
        self.error_handling = config.get("error_handling", {})
        self.error_topic = config.get("mqtt", {}).get("publish", {}).get("errors", {})

    def handle_error(self, error_message):
        """
        Handle an error by logging, publishing, transitioning states, and restarting if needed.

        Args:
            error_message (str): The error message to handle.
        """
        # Log the error
        self.logger.log_error(f"Handling error: {error_message}")

        # Publish error if configured
        if self.error_handling.get("post_global_errors", DEFAULT_POST_GLOBAL_ERROR) and self.mqtt_manager is not None:
            self.logger.log_debug("Publishing error to global errors topic.")

            if self.error_topic:
                self.logger.log_debug(f"Publishing error to topic {self.error_topic}: {error_message}")
                payload = json.dumps({"error": error_message, "timestamp": get_formatted_datetime()})
                self.mqtt_manager.publish(self.error_topic, payload)
            else:
                self.logger.log_error("No error topic configured, not publishing error.")
        else:
            self.logger.log_debug("Not publishing error to global errors topic.")

        # Restart if auto-restart is enabled
        if self.error_handling.get("auto_restart_on_error", DEFAULT_AUTO_RESTART_ON_ERROR):
            self.logger.log_info("Auto-restarting system due to error.")
            self.power.reboot()
        else:
            self.logger.log_info("Not auto-restarting system due to error.")
