import machine
import src.utils.logger as logger


class Watchdog:
    def __init__(self, config, logger):
        """
        Initialize the watchdog timer.

        Args:
            config (dict): Configuration containing the watchdog timeout.
            logger (Logger): Logger instance for logging messages.
        """

        self.watchdog_timeout = config.get_system_config().get("watchdog_timeout", 0)
        self.logger = logger

        if self.watchdog_timeout is not None and self.watchdog_timeout > 0:
            if self.watchdog_timeout > 8388607:
                self.logger.log_error("Watchdog timeout value is too large. Setting to maximum value.")
                self.watchdog_timeout = 8388607

            self._wdt = machine.WDT(timeout=self.watchdog_timeout)
            self.logger.log_info(f"Initializing Watchdog with {self.watchdog_timeout} ms timeout.")
        else:
            self.logger.log_info("Watchdog disabled.")

    def feed(self):
        """
        Reset the watchdog timer to prevent a reset.
        """
        if self.watchdog_timeout is not None and self.watchdog_timeout > 0:
            self._wdt.feed()
            self.logger.log_debug("Watchdog timer fed.")
        else:
            self.logger.log_debug("Watchdog disabled, no feeding required.")

