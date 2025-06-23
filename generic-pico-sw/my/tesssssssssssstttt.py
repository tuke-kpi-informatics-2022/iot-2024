import math
from machine import ADC
import time
from src.utils.logger import Logger
from src.utils.config import Config

class MQ135:
    """
    Class for dealing with MQ135 Gas Sensors using a 16-bit ADC and configurable
    load resistor/voltage divider approach.
    """

    # -------------------
    # Default Constants
    # -------------------

    # Default load resistance on the board, in kΩ (some boards mark it as 10 kΩ).
    DEFAULT_RLOAD = 10.0

    # Calibration resistance at atmospheric CO2 level
    RZERO = 76.63

    # Parameters for calculating ppm of CO2 from sensor resistance
    PARA = 116.6020682
    PARB = 2.769034857

    # Parameters to model temperature and humidity dependence
    CORA = 0.00035
    CORB = 0.02718
    CORC = 1.39538
    CORD = 0.0018
    CORE = -0.003333333
    CORF = -0.001923077
    CORG = 1.130128205

    # Atmospheric CO2 level for calibration purposes
    ATMOCO2 = 397.13

    # For a 16-bit ADC in MicroPython (range: 0–65535)
    MAX_ADC = 65535

    def __init__(self, pin,
                 board_resistance=DEFAULT_RLOAD,
                 base_voltage=3.3,
                 divider_ratio=1.0):
        """
        :param pin:          ADC pin to which the MQ135 sensor output is connected.
        :param board_resistance:  The load resistance (kΩ) on the MQ135 module (default ~10 kΩ).
        :param base_voltage: System operating voltage (e.g., 3.3 V on many MCUs).
        :param divider_ratio: If your hardware has an external voltage divider in series,
                              set this ratio accordingly. For example, if the sensor output is
                              further divided by a factor of 3, use divider_ratio=1/3.
        """
        self.adc = ADC(pin)
        self.board_resistance = board_resistance
        self.base_voltage = base_voltage
        self.divider_ratio = divider_ratio

    def _read_voltage(self):
        """
        Read the sensor output as a voltage (accounting for a 16-bit ADC and any
        configured external voltage divider).
        """
        raw_adc = self.adc.read_u16()  # 0 to 65535
        # Convert raw ADC reading to the actual voltage on the MQ135 sensor output pin
        v_out = (raw_adc * (self.base_voltage / self.MAX_ADC)) / self.divider_ratio
        return v_out

    def get_resistance(self):
        """
        Returns the resistance of the sensor in kΩ. If the output voltage is effectively 0,
        returns -1 to indicate an invalid reading.
        """
        v_out = self._read_voltage()
        if v_out <= 0:
            return -1

        # Sensor resistance formula:
        #     R_S = (V_supply - V_out) / V_out * R_load
        # Make sure to keep units consistent (kΩ).
        r_s = ((self.base_voltage - v_out) / v_out) * self.board_resistance
        return r_s

    def get_correction_factor(self, temperature, humidity):
        """
        Calculates the correction factor for ambient air temperature and relative humidity
        based on the linearization provided by Balk77.

        :param temperature: Ambient temperature in °C
        :param humidity:    Relative humidity in %
        :return:            A correction factor to apply to sensor resistance
        """
        if temperature < 20:
            return (self.CORA * temperature * temperature
                    - self.CORB * temperature
                    + self.CORC
                    - (humidity - 33.0) * self.CORD)
        return (self.CORE * temperature
                + self.CORF * humidity
                + self.CORG)

    def get_corrected_resistance(self, temperature, humidity):
        """
        Returns the sensor resistance corrected for temperature/humidity.
        """
        resistance = self.get_resistance()
        correction_factor = self.get_correction_factor(temperature, humidity)
        if correction_factor == 0:
            return -1
        return resistance / correction_factor

    def get_ppm(self):
        """
        Returns the ppm of CO2 sensed (assuming only CO2 in the air).
        """
        resistance = self.get_resistance()
        if resistance < 0:
            return -1
        return self.PARA * math.pow((resistance / self.RZERO), -self.PARB)

    def get_corrected_ppm(self, temperature, humidity):
        """
        Returns the ppm of CO2 sensed (assuming only CO2 in the air),
        corrected for temperature/humidity.
        """
        corrected_res = self.get_corrected_resistance(temperature, humidity)
        if corrected_res < 0:
            return -1
        return self.PARA * math.pow((corrected_res / self.RZERO), -self.PARB)

    def get_rzero(self):
        """
        Returns the sensor-specific RZero (in kΩ), which can be used for calibration.
        """
        resistance = self.get_resistance()
        if resistance < 0:
            return -1
        # RZero is defined for the atmospheric CO2 level (ATMOCO2).
        return resistance * math.pow((self.ATMOCO2 / self.PARA), (1.0 / self.PARB))

    def get_corrected_rzero(self, temperature, humidity):
        """
        Returns the sensor-specific RZero (in kΩ), corrected for temperature/humidity.
        Useful for calibration routines.
        """
        corrected_res = self.get_corrected_resistance(temperature, humidity)
        if corrected_res < 0:
            return -1
        return corrected_res * math.pow((self.ATMOCO2 / self.PARA), (1.0 / self.PARB))
    
if __name__ == "__main__":
    
    #Load configuration
    config = Config()

    # Initialize logger
    logger = Logger(config)
    # Suppose your MQ135 is connected to ADC pin 26
    SENSOR_PIN = 27

    # Create an instance with a known RLOAD=10 kΩ, system voltage=3.3 V, 
    # and no additional external divider (divider_ratio=1.0).
    mq135 = MQ135(pin=SENSOR_PIN,
                  board_resistance=10.0,   # 10 kΩ
                  base_voltage=3.3,
                  divider_ratio=1.0)

    # Simple loop to read and display CO2 in ppm
    while True:
        # If you have temperature & humidity from another sensor,
        # you can use get_corrected_ppm(temp, hum). 
        # For demonstration, let's assume 20 °C, 65% humidity:

        co2_ppm = mq135.get_corrected_ppm(temperature=20, humidity=65)
        rzero = mq135.get_corrected_rzero(temperature=20, humidity=65)

        print("CO2 (corrected) = {:.2f} ppm".format(co2_ppm))
        print("Calculated RZero (corrected) = {:.2f} kΩ".format(rzero))
        time.sleep(1)
