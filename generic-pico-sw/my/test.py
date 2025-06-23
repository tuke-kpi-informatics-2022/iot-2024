import math
from machine import ADC
import time

# MQ-135 Constants
PARA = 116.6020682  # CO2 curve parameters
PARB = 2.769034857
CORA = 0.00035
CORB = 0.02718
CORC = 1.39538
CORD = 0.0018
CORE = -0.003333333
CORF = -0.001923077
CORG = 1.130128205
ATMOCO2 = 415.58  # ppm

class MQ135:
    def __init__(self, pin_analog1, pin_analog2=None, rzero=76.63, rload=10.0, powered_via_3v3=True, v_div_ratio=1.0):
        self.adc1 = ADC(pin_analog1)
        self.adc2 = ADC(pin_analog2) if pin_analog2 is not None else None
        self.rzero = rzero
        self.rload = rload
        self.powered_via_3v3 = powered_via_3v3
        self.v_div_ratio = v_div_ratio

    def get_correction_factor(self, t_celsius, humidity):
        if t_celsius < 20:
            return CORA * t_celsius ** 2 - CORB * t_celsius + CORC - (humidity - 33) * CORD
        return CORE * t_celsius + CORF * humidity + CORG

    def get_average_adc_reading(self, samples=20, delay=0.02):
        total = 0
        for _ in range(samples):
            val1 = self.adc1.read_u16() / 65535.0
            val2 = self.adc2.read_u16() / 65535.0 if self.adc2 else 0
            total += (val1 + val2) / (2 if self.adc2 else 1)
            time.sleep(delay)
        return total / samples

    def get_resistance(self):
        adc_ratio = self.get_average_adc_reading()
        if adc_ratio <= 0:
            return float('inf')
        v_out = (3.3 * adc_ratio) * self.v_div_ratio
        v_in = 3.3 if self.powered_via_3v3 else 5.0
        if v_out <= 0:
            return float('inf')
        return (v_in / v_out - 1.0) * self.rload

    def get_corrected_resistance(self, t_celsius, humidity):
        correction = self.get_correction_factor(t_celsius, humidity)
        return self.get_resistance() / correction

    def get_ppm(self):
        rs = self.get_resistance()
        if rs <= 0:
            return 0
        return PARA * math.pow((rs / self.rzero), -PARB)

    def get_corrected_ppm(self, t_celsius, humidity):
        rs_corr = self.get_corrected_resistance(t_celsius, humidity)
        if rs_corr <= 0:
            return 0
        return PARA * math.pow((rs_corr / self.rzero), -PARB)

    def get_rzero(self):
        rs = self.get_resistance()
        if rs <= 0:
            return float('inf')
        return rs * math.pow((ATMOCO2 / PARA), (1.0 / PARB))

    def get_corrected_rzero(self, t_celsius, humidity):
        rs_corr = self.get_corrected_resistance(t_celsius, humidity)
        if rs_corr <= 0:
            return float('inf')
        return rs_corr * math.pow((ATMOCO2 / PARA), (1.0 / PARB))

# Main Function
if __name__ == "__main__":
    SENSOR_PIN1 = 26
    SENSOR_PIN2 = 27  # Optional, set to None if unused
    mq135 = MQ135(SENSOR_PIN1, SENSOR_PIN2, powered_via_3v3=True, v_div_ratio=1.0)
    temperature = 25.0  # °C
    humidity = 50.0  # %

    print("Warming up sensor...")
    time.sleep(2)  # Warm-up time for stable readings

    print("Calibrating RZero...")
    mq135.rzero = mq135.get_rzero()
    print(f"Calibrated RZero: {mq135.rzero:.2f} kΩ")

    def low_pass_filter(new_value, prev_value, alpha=0.1):
        """Simple low-pass filter for smoothing readings."""
        return alpha * new_value + (1 - alpha) * prev_value

    filtered_ppm = 0
    while True:
        rs = mq135.get_resistance()
        corrected_rs = mq135.get_corrected_resistance(temperature, humidity)
        ppm = mq135.get_ppm()
        corrected_ppm = mq135.get_corrected_ppm(temperature, humidity)

        # Apply low-pass filter
        filtered_ppm = low_pass_filter(corrected_ppm, filtered_ppm)

        print("----------------------------------------------------")
        print(f"Resistance: {rs:.2f} kΩ")
        print(f"Corrected Resistance: {corrected_rs:.2f} kΩ")
        print(f"CO2 (PPM): {ppm:.2f}")
        print(f"Corrected CO2 (PPM): {corrected_ppm:.2f}")
        print(f"Smoothed CO2 (PPM): {filtered_ppm:.2f}")
        time.sleep(1)
