    """Micropython library for dealing with MQ135 gas sensor
    Based on Arduino Library developed by G.Krocker (Mad Frog Labs)
    and the corrections from balk77 and ViliusKraujutis

    More info:
        https://hackaday.io/project/3475-sniffing-trinket/log/12363-mq135-arduino-library
        https://github.com/ViliusKraujutis/MQ135
        https://github.com/balk77/MQ135
    """

    import math
    import time
    from machine import ADC

    class MQ135(object):
        """ Class for dealing with MQ13 Gas Sensors """
        # The load resistance on the board
        RLOAD = 10.0
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


        def __init__(self, pin):
            self.pin = pin

        def get_correction_factor(self, temperature, humidity):
            """Calculates the correction factor for ambient air temperature and relative humidity

            Based on the linearization of the temperature dependency curve
            under and above 20 degrees Celsius, asuming a linear dependency on humidity,
            provided by Balk77 https://github.com/GeorgK/MQ135/pull/6/files
            """

            if temperature < 20:
                return self.CORA * temperature * temperature - self.CORB * temperature + self.CORC - (humidity - 33.) * self.CORD

            return self.CORE * temperature + self.CORF * humidity + self.CORG

        def get_resistance(self):
            """Returns the resistance of the sensor in kOhms // -1 if not value got in pin"""
            adc = ADC(self.pin)
            value = adc.read_u16()
            if value == 0:
                return -1

            return (1023./value - 1.) * self.RLOAD

        def get_corrected_resistance(self, temperature, humidity):
            """Gets the resistance of the sensor corrected for temperature/humidity"""
            return self.get_resistance()/ self.get_correction_factor(temperature, humidity)

        def get_ppm(self):
            """Returns the ppm of CO2 sensed (assuming only CO2 in the air)"""
            return self.PARA * math.pow((self.get_resistance()/ self.RZERO), -self.PARB)

        def get_corrected_ppm(self, temperature, humidity):
            """Returns the ppm of CO2 sensed (assuming only CO2 in the air)
            corrected for temperature/humidity"""
            return self.PARA * math.pow((self.get_corrected_resistance(temperature, humidity)/ self.RZERO), -self.PARB)

        def get_rzero(self):
            """Returns the resistance RZero of the sensor (in kOhms) for calibratioin purposes"""
            return self.get_resistance() * math.pow((self.ATMOCO2/self.PARA), (1./self.PARB))

        def get_corrected_rzero(self, temperature, humidity):
            """Returns the resistance RZero of the sensor (in kOhms) for calibration purposes
            corrected for temperature/humidity"""
            return self.get_corrected_resistance(temperature, humidity) * math.pow((self.ATMOCO2/self.PARA), (1./self.PARB))
        
