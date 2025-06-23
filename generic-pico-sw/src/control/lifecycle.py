from src.control.device_state import DeviceState
from src.utils.logger import Logger

class Lifecycle:
    def __init__(self, logger, state_manager):
        """
        Initialize the Lifecycle object.

        Args:
            logger (Logger): Logger instance to log lifecycle transitions.
            state_manager (StateManager): Object to handle state transitions.
        """

        self.logger = logger
        self.state_manager = state_manager
        self.current_state = DeviceState.INACTIVE
        self.logger.log_info(f"Lifecycle initialized in state: {self.current_state}")

    def transition_to(self, new_state):
        """
        Transition the lifecycle to a new state.

        Args:
            new_state (str): The new state to transition to.
        """

        self.logger.log_info(f"Lifecycle: {self.current_state} -> {new_state}")
        self.current_state = new_state
        self.state_manager.handle_state_change(new_state)
