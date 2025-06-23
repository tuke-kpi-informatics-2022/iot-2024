import ujson
import os
from src.defaults import DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_DEFAULT_PATH

class Config: 
    def __init__(self, path=DEFAULT_CONFIG_PATH):
        self.path = path
        self.data = self.load_config()


    def load_config(self):
        """
        Loads a JSON configuration file from 'path'.

        Args:
            path (str): Path to the configuration file.

        Returns:
            dict: Parsed configuration data.

        Raises:
            OSError: If the file cannot be found or read.
            ValueError: If the file content is not valid JSON or is not a dictionary.
        """
        # Check if the file exists
        try:
            with open(self.path, "r") as f:
                data = ujson.load(f)
            # Validate that the loaded data is a dictionary
            if not isinstance(data, dict):
                raise ValueError(f"Configuration file content at {self.path} is not a dictionary.")
            return data
        except OSError:
            raise OSError(f"Configuration file not found or inaccessible at {self.path}.")
        except ValueError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
        
    def save_config(self):
        """
        Saves the current configuration data to the configuration file.

        Raises:
            OSError: If the file cannot be written.
        """
        try:
            with open(self.path, "w") as f:
                ujson.dump(self.data, f)
        except OSError:
            raise OSError(f"Configuration file not found or inaccessible at {self.path}.")

    def reset_config(self):
        """
        Resets the configuration data to the default values.
        """
        # Check if the file exists
        try:
            with open(DEFAULT_CONFIG_DEFAULT_PATH, "r") as f:
                data = ujson.load(f)
   
            # Validate that the loaded data is a dictionary
            if not isinstance(data, dict):
                raise ValueError(f"Configuration file content at {self.path} is not a dictionary.")

            self.data = data
            self.save_config()

        except OSError:
            raise OSError(f"Configuration file not found or inaccessible at {self.path}.")
        except ValueError as e:
            raise ValueError(f"Error parsing configuration file: {e}")

    def get_wifi_config(self):
        return self.data.get('wifi', {})
    
    def get_mqtt_config(self):
        return self.data.get('mqtt', {})
    
    def get_system_config(self):
        return self.data.get('system', {})

    def get_system_power_config(self):
        return self.data.get('system', {}).get('power', {})
    
    def get_logging_config(self):
        return self.data.get('logging', {})
    
    def get_sensors(self):
        return self.data.get('sensors', {})
    
    def get_service_led(self):
        return self.data.get('service_led', {})
    
    def get_watchdog_config(self):
        return self.data.get('watchdog', {})
    

