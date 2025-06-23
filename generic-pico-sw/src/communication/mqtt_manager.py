from src.utils.logger import Logger
from umqtt.simple import MQTTClient

class MQTTManager:
    def __init__(self, mqtt_config, logger):
        """
        Initialize the MQTTManager with configuration and logger.

        Args:
            mqtt_config (dict): Configuration for MQTT client.
            logger: Logger instance for logging MQTT events.
        """

        self.config = mqtt_config
        self.client = MQTTClient(
            client_id=mqtt_config.get("client_id"),
            server=mqtt_config.get("server"),
            port=mqtt_config.get("port"),
            user=mqtt_config.get("user"),
            password=mqtt_config.get("password")
        )
        self.logger = logger
        self.logger.log_info("MQTTManager: initializing...")
        self.connected = False
        self.callbacks = {}  # Store callbacks for each topic

    def connect(self):
        """
        Connect to the MQTT broker.
        """
    
        self.logger.log_info("MQTTManager: connecting...")
    
        try:
            self.client.connect()
            self.connected = True
            self.logger.log_info("MQTT connected.")

        except Exception as e:
            self.logger.log_error(f"MQTT connection error: {e}")
            raise

    def check_messages(self):
        """
        Check for incoming MQTT messages (non-blocking).
        """
    
        if not self.connected:
            return

        try:
            self.client.check_msg()

        except Exception as e:
            self.logger.log_error(f"MQTT check_msg error: {e}")
            self.connected = False
            raise

    def publish(self, topic, message):
        """
        Publish a message to a specified MQTT topic.

        Args:
            topic (str): Topic to publish the message to.
            message (str): Message payload.
        """

        if not self.connected:
            self.logger.log_warning("MQTT not connected. Publish aborted.")
            return

        self.logger.log_debug(f"MQTT publish -> {topic}: {message}")

        try:
            self.client.publish(topic, message)

        except Exception as e:
            self.logger.log_error(f"MQTT publish error: {e}")
            raise

    def subscribe(self, topic, callback):
        """
        Subscribe to a specified MQTT topic with a custom callback.

        Args:
            topic (str): Topic to subscribe to.
            callback (function): Function to handle incoming messages on the topic.
        """

        if not self.connected:
            self.logger.log_warning("MQTT not connected. Subscribe aborted.")
            return

        self.logger.log_debug(f"MQTT subscribe -> {topic}")

        try:
            self.callbacks[topic] = callback
            self.client.set_callback(self._message_router)
            self.client.subscribe(topic)

        except Exception as e:
            self.logger.log_error(f"MQTT subscribe error: {e}")
            raise

    def _message_router(self, topic, msg):
        """
        Route incoming messages to the appropriate callback based on the topic.

        Args:
            topic (bytes): Topic of the message.
            msg (bytes): Message payload.
        """
        topic_str = topic.decode("utf-8")
        self.logger.log_debug(f"MQTT message received -> {topic_str}: {msg}")

        if topic_str in self.callbacks:
            try:
                self.callbacks[topic_str](topic_str, msg)
            except Exception as e:
                self.logger.log_error(f"Error in callback for topic {topic_str}: {e}")
        else:
            self.logger.log_warning(f"No callback registered for topic: {topic_str}")