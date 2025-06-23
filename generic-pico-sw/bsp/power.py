import json
import picosleep
import machine
from src.defaults import DEFAULT_DEEP_SLEEP_INTERVAL

class Power:
    def __init__(self, config, logger):
        """
        Initialize the Power manager with a configuration dict and a logger.

        Args:
            config (dict): A dictionary containing power-related configuration.
                           Expected key: "deep_sleep_interval_s" (int).
            logger: A logger instance to record info, debug, and error messages.
        """

        self.deep_sleep_interval_s = config.get_system_power_config().get("deep_sleep_interval_s", DEFAULT_DEEP_SLEEP_INTERVAL)
        self.components = {}
        self.logger = logger
        self.logger.log_info(f"PowerManager initialized with deep sleep interval: {self.deep_sleep_interval_s} s.")

    def add_component(self, disable_handler):
        """
        Register a disable-handler function that will be called before deep sleep.

        Args:
            disable_handler (callable): A function that disables a specific component.
                                        For example, turning off a sensor or peripheral.
        """

        name = disable_handler.__name__
        self.components[name] = disable_handler
        self.logger.log_info(f"Component '{name}' added to PowerManager.")

    def prepare_for_sleep(self):
        """
        Calls each registered disable-handler, preparing the system for deep sleep.
        """

        self.logger.info("Preparing system for deep sleep...")

        for name, disable_handler in self.components.items():
            try:
                disable_handler()
                self.logger.debug(f"Disabled component '{name}'.")
            except Exception as e:
                self.logger.log_error(f"Failed to disable component '{name}': {e}")
                raise

    def deep_sleep(self):
        """
        Put the device into deep sleep for the configured interval.

        - Disables all registered components.
        - Calls picosleep.seconds() to actually sleep.
        """

        self.logger.log_info(f"Entering deep sleep for {self.deep_sleep_interval_s} seconds...")
        self.prepare_for_sleep()

        try:
        #     # picosleep.seconds() blocks for the specified duration,
        #     # then the device wakes (or resets, depending on board/firmware behavior).
            picosleep.seconds(self.deep_sleep_interval_s)
        except Exception as e:
            self.logger.log_error(f"Failed to enter deep sleep: {e}")
            raise

    def reboot(self):
        """
        Reboot the device using machine.reset().
        """

        self.logger.log_info("Rebooting device...")
        machine.reset()

    def shutdown(self):
        """
        Shutdown the device by entering deep sleep
        with an infinite sleep interval.
        """

        import sys
        sys.exit()