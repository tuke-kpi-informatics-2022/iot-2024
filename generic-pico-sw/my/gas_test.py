import math
from machine import ADC
import time

import time
from src.utils.logger import Logger
from src.utils.config import Config

# MQ-135 Constants
PARA = 116.6020682
PARB = 2.769034857
CORA = 0.00035
CORB = 0.02718
CORC = 1.39538
CORD = 0.0018
CORE = -0.003333333
CORF = -0.001923077
CORG = 1.130128205
ATMOCO2 = 415.58

class MQ135:
    def __init__(self, pin_analog1, pin_analog2=None, rzero=76.63, rload=10.0):
        self.adc1 = ADC(pin_analog1)
        self.adc2 = ADC(pin_analog2) if pin_analog2 is not None else None
        self.rzero = rzero
        self.rload = rload
        self.divider_ratio = 1 / 3  # Adjust for 3x10 kΩ divider (⅓ scaling)

    def get_correction_factor(self, t, h):
        if t < 20:
            return CORA * t ** 2 - CORB * t + CORC - (h - 33) * CORD
        return CORE * t + CORF * h + CORG

    def get_average_adc_reading(self, samples=10, delay=0.01):
        total = 0
        for _ in range(samples):
            val1 = self.adc1.read_u16() / 65535.0
            val2 = self.adc2.read_u16() / 65535.0 if self.adc2 else val1
            total += (val1 + val2) / 2.0
            time.sleep(delay)
        return total / samples

    def get_resistance(self):
        adc_ratio = self.get_average_adc_reading()
        if adc_ratio <= 0:
            return float('inf')
        v_out = 3.3 * adc_ratio / self.divider_ratio  # Account for divider
        if v_out <= 0:
            return float('inf')
        return (5.0 / v_out - 1.0) * self.rload

    def get_corrected_resistance(self, t, h):
        correction = self.get_correction_factor(t, h)
        return self.get_resistance() / correction

    def get_ppm(self):
        rs = self.get_resistance()
        if rs <= 0:
            return 0
        return PARA * math.pow((rs / self.rzero), -PARB)

    def get_corrected_ppm(self, t, h):
        rs_corr = self.get_corrected_resistance(t, h)
        if rs_corr <= 0:
            return 0
        return PARA * math.pow((rs_corr / self.rzero), -PARB)

    def get_rzero(self):
        rs = self.get_resistance()
        if rs <= 0:
            return float('inf')
        return rs * math.pow((ATMOCO2 / PARA), (1.0 / PARB))

# Low-Pass Filter for Stability
def low_pass_filter(new_value, prev_value, alpha=0.2):
    return alpha * new_value + (1 - alpha) * prev_value

# Main Function
if __name__ == "__main__":
    
    #Load configuration
    config = Config()

    # Initialize logger
    logger = Logger(config)

    SENSOR_PIN1 = 27
    mq135 = MQ135(SENSOR_PIN1)

    temperature = 23.0
    humidity = 50.0

    print("Warming up the sensor...")
    time.sleep(1)

    print("Calibrating sensor in fresh air...")
    mq135.rzero = mq135.get_rzero()
    logger.log_info(f"Calibrated RZero: {mq135.rzero:.f} kΩ")
    
    print(f"Calibrated RZero: {mq135.rzero:.2f} kΩ")

    filtered_ppm = 0

    while True:
        resistance = mq135.get_resistance()
        corrected_resistance = mq135.get_corrected_resistance(temperature, humidity)

        ppm = mq135.get_ppm()
        corrected_ppm = mq135.get_corrected_ppm(temperature, humidity)

        # Smooth the PPM readings using a low-pass filter
        filtered_ppm = low_pass_filter(corrected_ppm, filtered_ppm)

        print(f"Resistance: {resistance:.2f} kΩ")
        print(f"Corrected Resistance: {corrected_resistance:.2f} kΩ")
        print(f"PPM: {ppm:.2f}")
        print(f"Corrected PPM: {corrected_ppm:.2f}")
        print(f"Filtered PPM: {filtered_ppm:.2f}")
        print("-" * 40)

        time.sleep(1)