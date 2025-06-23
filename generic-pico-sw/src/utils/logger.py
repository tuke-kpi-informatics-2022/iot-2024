# src/logger.py
import time


class Logger:
    LEVEL_MAP = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

    def __init__(self, config):
        """
        Initialize the logger with a configuration dict.

        Args:
            config (dict): Configuration dictionary for logger settings.
        """

        self.level = config.get_logging_config().get("level", "INFO").upper()
        self.log_to_file = config.get_logging_config().get("log_to_file", False)
        self.log_to_console = config.get_logging_config().get("log_to_console", True)
        self.log_file_path = config.get_logging_config().get("log_file_path", "device.log")
        self.min_level_num = self.LEVEL_MAP.get(self.level, 20)

    def _should_log(self, level_str):
        """
        Determine if a message should be logged based on the level.

        Args:
            level_str (str): The log level as a string.

        Returns:
            bool: True if the message should be logged, False otherwise.
        """

        return self.LEVEL_MAP.get(level_str.upper(), 50) >= self.min_level_num

    def _write_log(self, message):
        """
        Write the log message to the appropriate destinations.

        Args:
            message (str): The log message.
        """

        if self.log_to_console:
            print(message)
        if self.log_to_file:
            try:
                with open(self.log_file_path, "a") as f:
                    f.write(message + "\n")
            except Exception as e:
                # Handle file write errors (optional logging)
                pass

    def log(self, level, message):
        """
        Log a message at the specified level.

        Args:
            level (str): The log level (e.g., "INFO", "DEBUG").
            message (str): The log message.
        """

        if self._should_log(level):
            ts = time.time()
            log_str = f"[{ts:.3f}] [{level}] {message}"
            self._write_log(log_str)

    def log_debug(self, msg):
        """
        Log a message at DEBUG level.

        Args:
            msg (str): The log message.
        """

        self.log("DEBUG", msg)

    def log_info(self, msg):
        """
        Log a message at INFO level.

        Args:
            msg (str): The log message.
        """

        self.log("INFO", msg)

    def log_warning(self, msg):
        """
        Log a message at WARNING level.

        Args:
            msg (str): The log message.
        """

        self.log("WARNING", msg)

    def log_error(self, msg):
        """
        Log a message at ERROR level.

        Args:
            msg (str): The log message.
        """

        self.log("ERROR", msg)

    def log_critical(self, msg):
        """
        Log a message at CRITICAL level.

        Args:
            msg (str): The log message.
        """

        self.log("CRITICAL", msg)
