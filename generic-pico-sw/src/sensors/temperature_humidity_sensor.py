import machine
import dht
import time
from src.sensors.base_sensor import BaseSensor

class TemperatureHumiditySensor(BaseSensor):
    def __init__(self, s_config, config, mqtt_manager, logger):
        super().__init__(s_config, config, mqtt_manager, logger)
        pin = s_config["args"]["pin"]
        self._dht_pin = machine.Pin(pin, machine.Pin.IN)
        self._dht = dht.DHT11(self._dht_pin)

    def read_values(self):
        try:
            self._dht.measure()
            temp_celsius = self._dht.temperature()
            hum_percentage = self._dht.humidity()

            # Determine temperature unit and convert accordingly
            temp_unit = self.parameters["editable"].get("unit_temperature", "Celsius")
            if temp_unit == "Fahrenheit":
                temperature = (temp_celsius * 9 / 5) + 32
            elif temp_unit == "Kelvin":
                temperature = temp_celsius + 273.15
            else:
                temperature = temp_celsius  # Default is Celsius

            # Determine humidity unit and convert accordingly
            hum_unit = self.parameters["editable"].get("unit_humidity", "percentage")
            if hum_unit == "fraction":
                humidity = hum_percentage / 100.0
            elif hum_unit == "per_mille":
                humidity = hum_percentage * 10
            else:
                humidity = hum_percentage  # Default is percentage (%)

            # Get the current datetime
            current_datetime = time.localtime()
            formatted_datetime = "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
                current_datetime[0], current_datetime[1], current_datetime[2],
                current_datetime[3], current_datetime[4], current_datetime[5]
            )

            return {
                "temperature": temperature,
                "humidity": humidity,
                "unit_temperature": temp_unit,
                "unit_humidity": hum_unit,
                "datetime": formatted_datetime
            }
        except Exception as e:
            err_topic = self.publish_topics.get("errors")
            self.logger.log_error(f"[{self.sensor_id}] read error: {e}")
            raise e
