from src.sensors.sensor import Sensor
from src.sensors.sensor_state import SensorState
from src.utils.logger import Logger

import json

class BaseSensor(Sensor):
    def __init__(self, s_config, config, mqtt_manager, logger):
        """
        Initialize the BaseSensor with configuration, MQTT manager, logger, and optional config updater.

        Args:
            config (dict): Sensor configuration containing details such as MQTT topics and parameters.
            mqtt_manager: MQTT manager for handling publish/subscribe operations.
            logger: Logger instance for recording sensor activities.
        """

        self.config = config
        self.mqtt_manager = mqtt_manager

        self.sensor_id = s_config.get("id")
        self.publish_topics = s_config.get("mqtt", {}).get("publish", {})
        self.subscribe_topics = s_config.get("mqtt", {}).get("subscribe", {})

        self.parameters = s_config.get("parameters", {})
        self.capabilities = s_config.get("capabilities", {})

        self._state = SensorState.ACTIVE  # Default state

        self.logger = logger 
        self.logger.log_info(f"[{self.sensor_id}] BaseSensor initialized.")
        self.publish_info()

    def initialize(self):
        """
        Perform sensor-specific initialization steps.
        Subclasses should override this method if hardware initialization is required.
        """

        pass

    def read_values(self):
        """
        Retrieve sensor readings.
        Subclasses must implement this method to return a dictionary of sensor data.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """

        raise NotImplementedError("Subclasses must implement 'read_values()'")

    def do_self_test(self):
        """
        Perform a self-test to verify sensor functionality.
        Subclasses can override this method to implement specific self-test logic.

        Returns:
            bool: True if the self-test passes, False otherwise.
        """
        self.logger.log_info(f"[{self.sensor_id}] Running self_test (base implementation).")

        # Example: Return True if self-test passes, else return False.
        return True

    def publish_data(self, data):
        """
        Publish sensor data to the configured "data" MQTT topic.

        Args:
            data (dict): The sensor data to publish.
        """

        if not self._can_publish(data):
            return

        topic = self.publish_topics.get("data")

        if topic and self.mqtt_manager:
            self.logger.log_debug(f"[{self.sensor_id}] publish_data -> {topic}: {data}")
            self.mqtt_manager.publish(topic, json.dumps(data).encode('utf-8'))
        else:
            self.logger.log_warning(f"[{self.sensor_id}] No data topic found.")

    def publish_error(self, data):
        """
        Publish an error message to the configured "errors" MQTT topic.

        Args:
            data (dict): The error message to publish.
        """

        if not self._can_publish(data):
            return

        topic = self.publish_topics.get("errors")

        if topic and self.mqtt_manager:
            self.logger.log_debug(f"[{self.sensor_id}] publish_error -> {topic}: {data}")
            self.mqtt_manager.publish(topic, json.dumps(data).encode('utf-8'))
        else:
            self.logger.log_warning(f"[{self.sensor_id}] No error topic found.")

    def publish_state(self):
        """
        Publish the sensor's current state (e.g., ACTIVE, DISABLED, ERROR) to the "state" MQTT topic.
        """
        
        topic = self.publish_topics.get("state")

        if topic and self.mqtt_manager:
            self.logger.log_debug(f"[{self.sensor_id}] publish_state -> {topic}: {self._state}")
            self.mqtt_manager.publish(topic, json.dumps({"state": self._state}).encode('utf-8'))
        else:
            self.logger.log_warning(f"[{self.sensor_id}] No state topic found.")

    def publish_info(self):
        """
        Publish read-only information (e.g., model, manufacturer) to the "info" MQTT topic.
        """

        topic = self.publish_topics.get("info")

        if topic and self.mqtt_manager:
            read_only = self.parameters.get("read_only", {})
            self.logger.log_debug(f"[{self.sensor_id}] publish_info -> {topic}: {read_only}")            
            self.mqtt_manager.publish(topic, json.dumps(read_only).encode('utf-8'))
        else:
            self.logger.log_warning(f"[{self.sensor_id}] No info topic found.")

    def process_command(self, command):
        """
        Process control commands such as enable, disable, self_test, or factory_reset.

        Args:
            command (json): The command to process.
        """

        command_map = {
            "enable": self.enable,
            "disable": self.disable,
            "self_test": self.do_self_test,
            "factory_reset": self._do_factory_reset
        }

        if command in self.capabilities.get("control", []) and command in command_map:
            self.logger.log_info(f"[{self.sensor_id}] Processing command '{command}'.")
            command_map[command]()
        else:
            self.logger.log_warning(f"[{self.sensor_id}] Unsupported command '{command}'.")

    def update_parameter(self, key, value):
        """
        Update a configurable parameter for the sensor.

        Args:
            key (str): The parameter to update.
            value: The new value for the parameter.
        """
        editable = self.parameters.get("editable", {})
        if key in editable:
            old_val = editable[key]
            editable[key] = value
            self.config.save_config()
            self.logger.log_info(f"[{self.sensor_id}] Updated parameter '{key}' from '{old_val}' to '{value}'")
            self.logger.log_info(f"[{self.sensor_id}] Configuration updated successfully.")
        else:
            self.logger.log_warning(f"[{self.sensor_id}] '{key}' is not in editable parameters.")

    def _do_factory_reset(self):
        """
        Reset all editable parameters to their factory default values.
        """
        fac_def = self.parameters.get("defaults", {})
        if not fac_def:
            self.logger.log_warning(f"[{self.sensor_id}] No 'factory_defaults' found.")
            return

        editable = self.parameters.get("editable", {})
        for k, default_val in fac_def.items():
            if k in editable:
                old_val = editable[k]
                editable[k] = default_val
                self.logger.log_info(f"[{self.sensor_id}] Reset '{k}' from '{old_val}' to default '{default_val}'")
                self.config.save_config()
            else:
                self.logger.log_warning(f"[{self.sensor_id}] '{k}' is not in editable parameters.")
              
        self.logger.log_info(f"[{self.sensor_id}] Factory reset completed.")
        self._state = SensorState.ACTIVE
        self.publish_state()

    def _can_publish(self, data):
        """
        Check if the sensor can publish data.
        """
        
        if not self.enabled:
            self.logger.log_warning(f"[{self.sensor_id}] Sensor is disabled. Skipping data publish.")
            return False
        
        if not data:
            self.logger.log_warning(f"[{self.sensor_id}] No data to publish.")
            return False
        
        if self._state is not SensorState.ACTIVE:
            self.logger.log_warning(f"[{self.sensor_id}] Sensor is not in ACTIVE state. Skipping data publish.")
            return False
        
        return True
    
    def enabled(self):
        return self._state is SensorState.ACTIVE

    def error(self):
        self._state = SensorState.ERROR
        self.publish_state()

    def enable(self):
        """
        Enable the sensor.
        """

        if self._state is SensorState.DISABLED:
            self.logger.log_info(f"[{self.sensor_id}] Enabling sensor.")
            self._state = SensorState.ACTIVE
            self.publish_state()

    def disable(self):
        """
        Disable the sensor.
        """

        if self._state is SensorState.ACTIVE:
            self.logger.log_info(f"[{self.sensor_id}] Disabling sensor.")
            self._state = SensorState.DISABLED
            self.publish_state()