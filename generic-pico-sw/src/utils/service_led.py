import uasyncio as asyncio
from machine import Pin
import neopixel


class ServiceLED:
    def __init__(self, config, logger):
        """
        Initializes the ServiceLED class with state-based configurations.

        Args:
            config (dict): Configuration dictionary for the service LED.
            logger: Logger instance for logging.
        """
        self.rgb_pin = config.get_service_led().get("pin")
        self.state_leds = config.get_service_led().get("state_leds")

        self.logger = logger
        self.logger.log_info(f"Service LED initialized on pin {self.rgb_pin}.")

        self.rgb_led = neopixel.NeoPixel(Pin(self.rgb_pin), 1)
        self.off_color = (0, 0, 0)  # Default off color
        self.rgb_led[0] = self.off_color
        self.rgb_led.write()

        # Store the current animation task
        self.current_task = None

    def indicate_state(self, state):
        """
        Indicate a system state using the configured LED settings.

        Args:
            state (str): The name of the state (e.g., "STARTUP", "ERROR").
        """

        state_config = self.state_leds.get(state)

        if not state_config:
            self.logger.log_info(f"No configuration found for state '{state}'.")
            return
        
        self.logger.log_info(f"Indicating state '{state}' with configuration: {state_config}")

        blink_pattern = state_config.get("blink_pattern")
        color = tuple(state_config.get("color"))
        times = state_config.get("times")
        self.logger.log_info( f"Indicating state '{state}' with color {color}, pattern {blink_pattern}, times {times}")

        if not blink_pattern or not color :
            self.logger.log_error(f"Invalid configuration for state '{state}'.")
            return

        if self.current_task:
            self.logger.log_debug("Cancelling ongoing LED animation.")
            self.current_task.cancel()

        loop = asyncio.get_event_loop()
        self.current_task = loop.create_task(self._animate_led(color, blink_pattern, times))

    async def _animate_led(self, color, blink_pattern, times):
        self.logger.log_debug(f"Starting LED animation with color {color}, pattern {blink_pattern}, times {times}.")
        try:
            iteration = 0
            while times == 0 or iteration < times:
                for duration in blink_pattern:
                    self.logger.log_debug(f"Setting LED to {color} for {duration}s.")
                    self.rgb_led[0] = color
                    self.rgb_led.write()
                    await asyncio.sleep(duration)
                    self.logger.log_debug(f"Turning LED off for {duration}s.")
                    self.rgb_led[0] = self.off_color
                    self.rgb_led.write()
                    await asyncio.sleep(duration)
                iteration += 1
        except asyncio.CancelledError:
            self.logger.log_debug("LED animation cancelled.")
        except Exception as e:
            self.logger.log_error(f"LED animation failed: {e}")
        finally:
            self.logger.log_info("LED animation finished.")
            self.rgb_led[0] = self.off_color
            self.rgb_led.write()


    def turn_off(self):
        """
        Turn off the NeoPixel LED.
        """

        self.logger.log_info("Turning off service LED.")
        self.rgb_led[0] = self.off_color
        self.rgb_led.write()
