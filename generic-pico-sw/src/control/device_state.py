class DeviceState:
    """
    Represents the various states of the device lifecycle.
    """

    STARTUP = "STARTUP" # Device is starting up, all initializations make here.

    ACTIVE = "ACTIVE" # Device is active and running.
    INACTIVE = "INACTIVE" # Device is inactive and running.

    ERROR = "ERROR" # Device is in error state, some error occurred, not sensor error.
    SLEEPING = "SLEEPING" # Device is in sleep state, running but sleeping.

    GLOBAL_ERROR = "GLOBAL_ERROR" # Device is in global error state so stop all operations.