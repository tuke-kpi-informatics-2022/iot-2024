import json
from src.control.device_state import DeviceState
from src.utils.logger import Logger

class StateManager:
    def __init__(self, service_led, logger, mqtt_manager, config):
        """
        Initialize the StateManager.

        Args:
            service_led: The LED manager.
            logger: Logger instance for logging state changes.
            mqtt_manager: MQTT manager for publishing state changes.
            system_config: The 'system' block from config.json.
        """

        self.service_led = service_led
        self.logger = logger
        self.mqtt_manager = mqtt_manager
        self.publish_state_topic = config.get_system_config().get("mqtt", {}).get("publish", {}).get("state", None)
        self.current_state = DeviceState.INACTIVE
        self.logger.log_info("StateManager: initializing...")

    def handle_state_change(self, new_state):
        """
        Handle state transition and update components.

        Args:
            new_state: The new state to transition to (DeviceState).
        """
    
        self.logger.log_info(f"StateManager: {self.current_state} -> {new_state}")
        self.current_state = new_state

        # Update LED state
        self.service_led.indicate_state(new_state)

        # Publish state change to MQTT
        if self.publish_state_topic is not None and self.mqtt_manager and self.mqtt_manager.connected:
            payload = {"state": new_state}
            self.logger.log_debug(f"Publishing device state to {self.publish_state_topic}: {payload}")
            self.mqtt_manager.publish(self.publish_state_topic, json.dumps(payload))
        else:
            self.logger.log_warning("MQTT not connected, state change not published")
