class MockLogger:
    def log_info(self, message):
        print(f"[INFO] {message}")

    def log_debug(self, message):
        print(f"[DEBUG] {message}")

    def log_error(self, message):
        print(f"[ERROR] {message}")

import uasyncio as asyncio
from machine import Pin
import neopixel

class ServiceLED:
    def __init__(self, config, logger):
        self.rgb_pin = config.get("pin")
        self.state_leds = config.get("state_leds")
        self.logger = logger
        self.logger.log_info(f"Service LED initialized on pin {self.rgb_pin}.")

        self.rgb_led = neopixel.NeoPixel(Pin(self.rgb_pin), 1)
        self.off_color = (0, 0, 0)
        self.rgb_led[0] = self.off_color
        self.rgb_led.write()
        self.current_task = None

    def indicate_state(self, state):
        state_config = self.state_leds.get(state)
        if not state_config:
            self.logger.log_info(f"No configuration found for state '{state}'.")
            return

        blink_pattern = state_config.get("blink_pattern")
        color = tuple(state_config.get("color"))
        times = state_config.get("times")

        if not blink_pattern or not color:
            self.logger.log_error(f"Invalid configuration for state '{state}'.")
            return

        if self.current_task:
            self.logger.log_debug("Cancelling ongoing LED animation.")
            self.current_task.cancel()

        self.logger.log_debug(f"Creating new task for state '{state}' with color {color}.")
        loop = asyncio.get_event_loop()
        self.current_task = loop.create_task(self._animate_led(color, blink_pattern, times))

    async def _animate_led(self, color, blink_pattern, times):
        self.logger.log_debug(f"Starting LED animation with color {color}, pattern {blink_pattern}, times {times}.")
        try:
            for _ in range(times):
                for duration in blink_pattern:
                    self.rgb_led[0] = color
                    self.rgb_led.write()
                    await asyncio.sleep(duration)
                    self.rgb_led[0] = self.off_color
                    self.rgb_led.write()
                    await asyncio.sleep(duration)
        except asyncio.CancelledError:
            self.logger.log_debug("LED animation cancelled.")
        finally:
            self.rgb_led[0] = self.off_color
            self.rgb_led.write()

class StateManager:
    def __init__(self, service_led, logger):
        self.service_led = service_led
        self.logger = logger

    def handle_state_change(self, state):
        self.logger.log_info(f"StateManager -> {state}")
        self.service_led.indicate_state(state)

class Lifecycle:
    def __init__(self, logger, state_manager):
        self.logger = logger
        self.state_manager = state_manager
        self.current_state = "OFFLINE"

    def transition_to(self, state):
        self.logger.log_info(f"Lifecycle: {self.current_state} -> {state}")
        self.current_state = state
        self.state_manager.handle_state_change(state)


class Application:
    def __init__(self):
        self.logger = MockLogger()

        config = {
            "pin": 28,
            "state_leds": {
                "STARTUP": {"color": [255, 0, 0], "blink_pattern": [0.5, 0.5], "times": 3},
                "INITIALIZING": {"color": [0, 0, 255], "blink_pattern": [1, 1], "times": 3},
                "ACTIVE": {"color": [0, 255, 0], "blink_pattern": [2, 2], "times": 0},
            },
        }

        self.service_led = ServiceLED(config, self.logger)
        self.state_manager = StateManager(self.service_led, self.logger)
        self.lifecycle = Lifecycle(self.logger, self.state_manager)

    async def run(self):
        self.lifecycle.transition_to("STARTUP")
        self.lifecycle.transition_to("STARTUP")
        self.lifecycle.transition_to("STARTUP")
        await asyncio.sleep(2)  # Simulate some startup delay
        self.lifecycle.transition_to("INITIALIZING")
        await asyncio.sleep(2)  # Simulate some initialization delay
        self.lifecycle.transition_to("ACTIVE")
        await asyncio.sleep(10)  # Keep active state for a while
        
import uasyncio as asyncio

async def main():
    app = Application()
    await app.run()

asyncio.run(main())

