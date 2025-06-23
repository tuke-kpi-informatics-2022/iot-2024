import json
import time
from src.utils.datetime import get_formatted_datetime
from src.defaults import DEFAULT_UPDATE_SENSOR_INTERVAL

class SensorManager:
    def __init__(self, config, mqtt_manager, logger, error_handler):
        """
        Initialize the SensorManager.

        Args:
            sensors_config (list): List of sensor configurations.
            mqtt_manager: MQTT manager for handling subscriptions and publications.
            config (dict): Full configuration dictionary.
            logger: Logger instance for logging events and errors.
        """
        self.config = config
        self.sensors_config = self.config.get_sensors()
        self.mqtt_manager = mqtt_manager
        self.sensors = {}  # Dictionary to store sensor instances
        self.logger = logger
        self.error_handler = error_handler

        # Dictionary to track next update times (in seconds).
        # Key: sensor_id, Value: next allowed update timestamp.
        self._next_update_times = {}
        self.logger.log_info("SensorManager initialized.")

    def initialize_sensors(self):
        """
        Load and initialize all sensors as specified in the configuration.
        This includes setting up MQTT subscriptions for commands and configurations.
        """
        for s_cfg in self.sensors_config:
            sid = s_cfg.get("id") 
            mod_name = s_cfg.get("module")
            class_name = s_cfg.get("class")
            
            try:
                # Dynamically import the sensor's module and class using __import__()
                module = __import__(f"src.sensors.{mod_name}")

                # Navigate to the submodule manually
                components = f"src.sensors.{mod_name}".split('.')
                for comp in components[1:]:  # Skip the first component ("src")
                    module = getattr(module, comp)
                SensorClass = getattr(module, class_name)
                self.logger.log_info(f"Sensor class {SensorClass}, Sensor module {module}")
                

                # Create an instance of the sensor
                sensor_instance = SensorClass(
                    s_config=s_cfg,
                    config=self.config,
                    mqtt_manager=self.mqtt_manager,
                    logger=self.logger
                )
    
                # Initialize the sensor (e.g., hardware or software setup)
                sensor_instance.initialize()
                self.sensors[sid] = sensor_instance

                # Set up MQTT subscriptions for the sensor
                sub_cfg = s_cfg.get("mqtt", {}).get("subscribe", {})

                if "commands" in sub_cfg:
                    self.logger.log_info(f"Sensor '{sid}' commands.")
                    self.logger.log_info(f"Sensor '{sid}' commands: {sub_cfg.get('commands')}")
                    self._subscribe(sub_cfg.get("commands"), self._make_cb(sid))
                
                if "config" in sub_cfg:
                    self.logger.log_info(f"Sensor '{sid}' config.")
                    self._subscribe(sub_cfg.get("config"), self._make_cb(sid))

                self._next_update_times[sid] = time.time()
                self.logger.log_info(f"Sensor '{sid}' initialized.")

            except Exception as e:
                self.error_handler.handle_error(f"Failed to load sensors: {e}")

    def update_sensors(self):
        """
        Update all sensors by reading their current values and publishing the data.
        Call this from your main loop or scheduler (e.g., every 10 second).
        """
        current_time = time.time()

        for sid, sensor in self.sensors.items():
            # Get custom interval or fall back to 10 seconds (or any default).
            interval = sensor.parameters.get("editable", {}).get("report_interval", DEFAULT_UPDATE_SENSOR_INTERVAL)
            if current_time >= self._next_update_times[sid]:
                try:

                    sensor.publish_state()  # Publish the sensor state
                    data = sensor.read_values()  # Retrieve sensor data
                    if data:
                        sensor.publish_data(data)  # Publish the data
                except Exception as e:
                    self.logger.log_error(f"[{sid}] Error during sensor update: {e}")
                    self._error_handler(sid, sensor, f"Error during sensor update: {e}")

                # Schedule the next update after the interval
                self._next_update_times[sid] = current_time + interval

    def get_sensor_ids(self):
        """
        Get a list of all initialized sensor IDs.

        Returns:
            list: List of sensor IDs.
        """
        return list(self.sensors.keys())

    def get_sensor_by_id(self, sid):
        """
        Retrieve a sensor instance by its ID.

        Args:
            sid (str): Sensor ID.

        Returns:
            Sensor: The sensor instance, or None if not found.
        """
        return self.sensors.get(sid)

    def _subscribe(self, topic, callback):
        """
        Subscribe to an MQTT topic with a specified callback.

        Args:
            topic (str): MQTT topic to subscribe to.
            callback (callable): Callback function to handle messages for the topic.
        """
        self.logger.log_debug(f"SensorManager subscribing to {topic}")
        self.mqtt_manager.subscribe(topic, callback)

    def _make_cb(self, sensor_id):
        """
        Create a unified callback for handling both commands and configurations via MQTT.

        Args:
            sensor_id (str): The sensor ID associated with the callback.

        Returns:
            callable: A callback function for processing messages.
        """
        def cb(topic, msg):
            sensor = self.sensors.get(sensor_id)
            if not sensor:
                self.logger.log_error(f"Sensor {sensor_id} not found.")
                return

            try:
                # Parse the incoming MQTT message as JSON
                parsed_msg = json.loads(msg.decode("utf-8"))
                self.logger.log_debug(f"[{sensor_id}] Message received on topic {topic}: {parsed_msg}")

                # Determine action based on topic
                if "commands" in topic:
                    # Handle commands
                    command = parsed_msg.get("command")
                    if not command:
                        self.logger.log_error(f"[{sensor_id}] No command found in message: {parsed_msg}")
                        return

                    self.logger.log_info(f"[{sensor_id}] Processing command: {command}")
                    sensor.process_command(command)

                elif "config" in topic:
                    # Handle configuration updates
                    if not isinstance(parsed_msg, dict):
                        self.logger.log_error(f"[{sensor_id}] Configuration is not a dictionary: {parsed_msg}")
                        return

                    self.logger.log_info(f"[{sensor_id}] Updating configuration: {parsed_msg}")

                    for key, value in parsed_msg.items():
                        sensor.update_parameter(key, value)

                    # If "report_interval" is updated, apply it immediately
                    if "report_interval" in parsed_msg:
                        self._next_update_times[sensor_id] = time.time() + parsed_msg["report_interval"]
                        self.logger.log_info(f"[{sensor_id}] Report interval updated: {parsed_msg['report_interval']}")

                else:
                    # Handle unexpected topics
                    self.logger.log_warning(f"[{sensor_id}] Unexpected topic: {topic}")

            except ValueError as e:
                self.logger.log_error(f"[{sensor_id}] Invalid JSON in message: {e}")
            except Exception as e:
                self.logger.log_error(f"[{sensor_id}] Error processing message: {e}")
                self._error_handler(sensor_id, sensor, f"Error processing message: {e}")

        return cb

    def _error_handler(self, sid, sensor, error_msg):
        """
        Handle errors that occur during sensor operations.

        Args:
            sid (str): Sensor ID.
            sensor (Sensor): Sensor instance.
            error_msg (str): Error message.
        """
        self.logger.log_error(f"Error in sensor {sid}")
        
        try:
            sensor.publish_error({"timestamp": get_formatted_datetime(), "error": error_msg})
            sensor.error()
            self.logger.log_info(f"Error data published for sensor {sid}")

        except Exception as e:
            self.logger.log_error(f"Error cannot be published for sensor {sid}: {e}, so disabling sensor.")
            
        