from src.utils.logger import Logger

import machine
import network
import time

class WiFiManager:
    def __init__(self, wifi_config, logger):
        """
        Initialize the WiFiManager with configuration and logger.

        Args:
            wifi_config (dict): Wi-Fi configuration containing SSID, password, and reconnect strategy.
            logger: Logger instance for logging Wi-Fi events.
        """
    
        self.config = wifi_config
        self.logger = logger
        self.logger.log_info("WiFiManager: initializing...")
        self.station = network.WLAN(network.STA_IF)
        self.station.active(True)

    def connect(self):
        """
        Connect to the Wi-Fi network using the provided configuration.
        """

        # SSID and password
        ssid = self.config.get("ssid")
        pwd = self.config.get("password")

        if not ssid or not pwd:
            self.logger.log_error("WiFiManager: missing SSID or password in configuration.")
            raise

        self.logger.log_info(f"WiFiManager: connecting to '{ssid}'")
        self.station.connect(ssid, pwd)

        # Reconnect strategy
        reconnect_strategy = self.config.get("reconnect_strategy", {})
        max_retries = reconnect_strategy.get("max_retries", 10)  # Default: 10 retries
        interval = reconnect_strategy.get("interval_seconds", 5)  # Default: 5 seconds 

        if (not max_retries or not interval) and (max_retries < 0 or interval < 0):
            self.logger.log_warning("WiFiManager: reconnect strategy not fully configured.")
            raise

        # Attempt to connect
        for attempt in range(max_retries):
            if self.station.isconnected():
                self.logger.log_info("Wi-Fi connected.")
                return
            time.sleep(interval)
            self.logger.log_info(f"Attempt {attempt+1} to connect WiFi.")

        # Reconnect failed
        action = reconnect_strategy.get("failure_action", "restart")
        self.logger.log_error(f"WiFi connect failed; action={action}")

        if action == "restart":
            self.logger.log_info("Restarting device...")
            machine.reset()
        elif action == "shutdown":
            self.logger.log_info("Shutting down device...")
            import sys
            sys.exit(1)
        elif action == "continue":
            self.logger.log_info("Continuing without Wi-Fi..., but this may cause issues.")
            pass

    def check_connection(self):
        """
        Check the Wi-Fi connection status and reconnect if necessary.
        """

        if not self.station.isconnected():
            self.logger.log_warning("Wi-Fi lost, reconnecting...")
            self.connect()

    def is_connected(self):
        """
        Check if the device is connected to the Wi-Fi network.

        Returns:
            bool: True if connected, False otherwise.
        """

        return self.station.isconnected()

    def disconnect(self):
        """
        Disconnect from the Wi-Fi network.
        """

        self.logger.log_info("Disconnecting from Wi-Fi...")
        self.station.disconnect()
        self.logger.log_info("Wi-Fi disconnected.")
