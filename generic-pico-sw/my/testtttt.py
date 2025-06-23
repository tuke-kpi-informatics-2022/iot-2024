import utime
from math import exp, log
from machine import ADC, Pin

class MQ7:
    """
    Unified MQ-7 sensor class with calibration, resistance measurement, 
    and gas reading (e.g., carbon monoxide) capabilities.
    """

    # Constants for the MQ-7 sensor
    DEFAULT_RO_BASE = 27.0           # Base RZero in clean air
    HEATING_PERIOD_MS = 60000       # Heating time in milliseconds
    COOLING_PERIOD_MS = 90000       # Cooling time in milliseconds
    SAMPLE_TIMES = 5                # Number of ADC samples for averaging
    SAMPLE_INTERVAL_MS = 500        # Time between samples in milliseconds

    def __init__(self, pin_data, board_resistance=10.0, base_voltage=3.3, divider_ratio=1.0, ro_base=None):
        """
        Initialize the MQ-7 sensor.

        :param pin_data: Analog pin connected to the sensor's output.
        :param board_resistance: Load resistance on the MQ-7 board, in kΩ.
        :param base_voltage: Operating voltage of the system (e.g., 3.3 V or 5.0 V).
        :param divider_ratio: Voltage divider ratio (e.g., 1/3 for 3x10kΩ resistors).
        :param ro_base: Optional initial RZero value for calibration.
        """
        self.pin_data = ADC(pin_data)
        self.board_resistance = board_resistance
        self.base_voltage = base_voltage
        self.divider_ratio = divider_ratio
        self.ro = ro_base or MQ7.DEFAULT_RO_BASE
        self.last_measurement_time = utime.ticks_ms()
        self._heater_on = False

    def _calculate_resistance(self, raw_adc):
        """Calculate sensor resistance (R_s) based on ADC reading."""
        v_out = raw_adc * (self.base_voltage / 65535) / self.divider_ratio
        if v_out <= 0:
            return float('inf')
        return (self.base_voltage - v_out) / v_out * self.board_resistance

    def _average_adc(self, samples=None, delay=None):
        """Average multiple ADC readings for better stability."""
        samples = samples or MQ7.SAMPLE_TIMES
        delay = delay or MQ7.SAMPLE_INTERVAL_MS
        total = 0.0
        for _ in range(samples):
            total += self.pin_data.read_u16()
            utime.sleep_ms(delay)
        return total / samples

    def calibrate(self):
        """
        Calibrate the sensor in clean air (approximately 0 ppm carbon monoxide).
        This updates the `ro` value based on current conditions.
        """
        print("Calibrating MQ-7 sensor in clean air...")
        avg_resistance = 0.0
        for _ in range(MQ7.SAMPLE_TIMES):
            avg_resistance += self._calculate_resistance(self.pin_data.read_u16())
            utime.sleep_ms(MQ7.SAMPLE_INTERVAL_MS)
        avg_resistance /= MQ7.SAMPLE_TIMES
        self.ro = avg_resistance / MQ7.DEFAULT_RO_BASE
        print(f"Calibration complete. RZero: {self.ro:.2f} kΩ")

    def read_resistance(self):
        """Measure the current resistance of the sensor."""
        raw_adc = self._average_adc()
        return self._calculate_resistance(raw_adc)

    def read_ratio(self):
        """Calculate the resistance ratio (R_s / R_0)."""
        rs = self.read_resistance()
        if self.ro <= 0 or rs <= 0:
            return float('inf')
        return rs / self.ro

    def read_carbon_monoxide(self):
        """
        Estimate carbon monoxide concentration in ppm.
        Uses the empirical formula for the MQ-7 sensor.
        """
        ratio = self.read_ratio()
        if ratio <= 0:
            return 0.0
        # Empirical curve constants for CO (from datasheet)
        CO_CURVE_A = -0.77
        CO_CURVE_B = 3.38
        return exp((log(ratio) - CO_CURVE_B) / CO_CURVE_A)

    def heater_cycle(self):
        """
        Control heater states for accurate CO measurements.
        Alternates between heating and cooling phases.
        """
        current_time = utime.ticks_ms()
        elapsed = utime.ticks_diff(current_time, self.last_measurement_time)

        if not self._heater_on and elapsed >= MQ7.COOLING_PERIOD_MS:
            # Turn heater ON (heating phase)
            print("Starting heating phase...")
            self._heater_on = True
            self.last_measurement_time = current_time
        elif self._heater_on and elapsed >= MQ7.HEATING_PERIOD_MS:
            # Turn heater OFF (cooling phase)
            print("Starting cooling phase...")
            self._heater_on = False
            self.last_measurement_time = current_time

    def read_sensor(self):
        """
        Perform a complete sensor reading cycle and print results.
        This handles the heater cycle, resistance measurement, and gas estimation.
        """
        self.heater_cycle()
        resistance = self.read_resistance()
        co_ppm = self.read_carbon_monoxide()
        print(f"Sensor Resistance: {resistance:.2f} kΩ")
        print(f"Carbon Monoxide: {co_ppm:.2f} ppm")

# Example usage
if __name__ == "__main__":
    SENSOR_PIN = 26  # ADC pin connected to MQ-7 output
    mq7 = MQ7(SENSOR_PIN, board_resistance=10.0, base_voltage=3.3, divider_ratio=1.0 / 3.0)

    print("Warming up the MQ-7 sensor...")
    utime.sleep(10)  # Warm-up period

    mq7.calibrate()

    while True:
        try:
            mq7.read_sensor()
            utime.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            utime.sleep(2)
