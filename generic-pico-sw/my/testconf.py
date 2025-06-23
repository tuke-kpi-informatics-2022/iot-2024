import os
import ujson
from pathlib import Path
from src.utils import load_config, save_config, update_config  # Replace 'your_module' with the module name containing your functions.

# Test Configuration Path
TEST_CONFIG_PATH = "test_config.json"

# Helper Functions for Tests
def write_test_config(config, path=TEST_CONFIG_PATH):
    with open(path, "w") as f:
        ujson.dump(config, f)

def read_test_config(path=TEST_CONFIG_PATH):
    with open(path, "r") as f:
        return ujson.load(f)

def delete_test_config(path=TEST_CONFIG_PATH):
    if Path(path).exists():
        os.remove(path)

# Test Function
def test_update_config():
    try:
        # Step 1: Write initial configuration
        initial_config = {
            "wifi": {
                "ssid": "putonatre",
                "password": "sarvatero",
                "reconnect_strategy": {
                    "interval_seconds": 10,
                    "max_retries": 10,
                    "failure_action": "restart"
                }
            },
            "mqtt": {
                "client_id": "pico_device_001",
                "server": "192.168.137.1",
                "port": 1883,
                "user": "",
                "password": ""
            }
        }
        write_test_config(initial_config)

        # Step 2: Define updates
        updates = {
            "wifi": {
                "ssid": "putonatrsde",
                "password": "sssss"
            }
        }

        # Step 3: Perform update
        update_config(updates, path=TEST_CONFIG_PATH)

        # Step 4: Validate the result
        expected_config = {
            "wifi": {
                "ssid": "putonatrsde",
                "password": "sssss",
                "reconnect_strategy": {
                    "interval_seconds": 10,
                    "max_retries": 10,
                    "failure_action": "restart"
                }
            },
            "mqtt": {
                "client_id": "pico_device_001",
                "server": "192.168.137.1",
                "port": 1883,
                "user": "",
                "password": ""
            }
        }

        updated_config = read_test_config()
        assert updated_config == expected_config, f"Test failed! Config mismatch: {updated_config}"

        print("Test passed! Configuration updated correctly.")
    
    except AssertionError as e:
        print(e)
    finally:
        # Cleanup: Delete test configuration file
        delete_test_config()

# Run the Test
if __name__ == "__main__":
    test_update_config()
