import sys
import uasyncio as asyncio
from src.utils.config import Config
from src.utils.logger import Logger
from src.control.error_handler import ErrorHandler
from src.utils.service_led import ServiceLED
from src.communication.wifi_manager import WiFiManager
from src.communication.mqtt_manager import MQTTManager
from src.sensors.sensor_manager import SensorManager
from src.control.lifecycle import Lifecycle
from src.control.state_manager import StateManager
from src.control.device_state import DeviceState
from src.defaults import (
    DEFAULT_WAIT_TIME_AFTER_STARTUP, 
    DEFAULT_WAIT_TIME_AFTER_ERROR, 
    DEFAULT_WAIT_TIME_AFTER_GLOBAL_ERROR
)
from bsp.power import Power
from bsp.watchdog import Watchdog
from src.control.system_manager import SystemManager

class Application:
    def __init__(self):
        try:
            # Load configuration
            self.config = Config()

            # Initialize logger
            self.logger = Logger(self.config)

            # Initialize service LED
            self.service_led = ServiceLED(self.config, self.logger)

            # Initialize power manager
            self.power = Power(self.config, self.logger)

            # Initialize watchdog
            self.watchdog = Watchdog(self.config, self.logger)

            # Initialize error handler
            self.error_handler = ErrorHandler(
                config=self.config.get_system_config(),
                power=self.power,
                lifecycle=None,
                mqtt_manager=None,
                logger=self.logger
            )
            
            self.logger.log_info("Initialization successful")
        except Exception as e:
            self.logger.log_error(f"Critical error during initialization: {e}")
            sys.exit()

        try:    
            # Initialize Wi-Fi and MQTT
            self.wifi_manager = WiFiManager(self.config.get_wifi_config(), self.logger)
            self.mqtt_manager = MQTTManager(self.config.get_mqtt_config(), self.logger)

            self.error_handler.mqtt_manager = self.mqtt_manager  # Assign MQTT manager to error handler

            # Initialize sensors
            self.sensor_manager = SensorManager(
                config=self.config,
                mqtt_manager=self.mqtt_manager,
                logger=self.logger,
                error_handler=self.error_handler
            )

            # Initialize state manager and lifecycle
            self.state_manager = StateManager(
                service_led=self.service_led,
                logger=self.logger,
                mqtt_manager=self.mqtt_manager,
                config=self.config
            )
            self.lifecycle = Lifecycle(self.logger, self.state_manager)
            self.error_handler.lifecycle = self.lifecycle  # Assign lifecycle to error handler

            # Initialize system manager
            self.system_manager = SystemManager(
                config=self.config,
                mqtt_manager=self.mqtt_manager,
                power=self.power,
                logger=self.logger,
                error_handler=self.error_handler
            )
        except Exception as e:
            self.error_handler.handle_error(f"Error during initialization: {e}")
            

    async def run(self):
        try:
            # STARTUP
            self.lifecycle.transition_to(DeviceState.STARTUP)
            await asyncio.sleep(DEFAULT_WAIT_TIME_AFTER_STARTUP)
            
            # Initialize system
            self._initialize_system()

            # ACTIVE
            self.lifecycle.transition_to(DeviceState.ACTIVE)

            # Main loop
            while True:
                self.watchdog.feed()

                self.wifi_manager.check_connection()
                self.mqtt_manager.check_messages()
                self.sensor_manager.update_sensors()

                await asyncio.sleep(10)
    
        except Exception as e:
            self.error_handler.handle_error(f"Error during main loop: {e}")

    def _initialize_system(self):
        self.wifi_manager.connect()
        self.mqtt_manager.connect()
        self.system_manager.initialize()
        self.sensor_manager.initialize_sensors()

    async def _handle_critical_error(self, e):
        self.logger.log_error(f"Critical error: {e}")

        if hasattr(self, "service_led"):
            self.service_led.indicate_state(DeviceState.GLOBAL_ERROR)
            await asyncio.sleep(DEFAULT_WAIT_TIME_AFTER_GLOBAL_ERROR)

        self.logger.log_error("System shutting down due to critical error.")
        sys.exit()
