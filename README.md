# Generic Pico Software - IoT 2024

This repository contains a generic software base for Raspberry Pi Pico (and compatible microcontrollers) used in IoT projects for the academic year 2024. It is designed to be modular, extensible, and easy to adapt for various sensor, actuator, and communication scenarios.

## Project Overview

This project provides a flexible foundation for developing IoT applications on the Raspberry Pi Pico platform using MicroPython. It includes drivers for common sensors, MQTT communication, WiFi management, and a structured approach to device state and lifecycle management.

## Features

- **Modular Sensor Support**: Easily add and manage sensors (e.g., gas, temperature, humidity)
- **MQTT Communication**: Built-in support for MQTT messaging
- **WiFi Management**: Simple WiFi connection and reconnection logic
- **Device State & Lifecycle**: Robust state management for reliable operation
- **Extensible Architecture**: Add your own sensors, actuators, and logic

## Repository Structure

```
generic-pico-sw/
├── bsp/                # Board support package (power, watchdog, etc.)
├── config/             # Configuration files (JSON)
├── lib/                # External libraries (e.g., umqtt)
├── my/                 # User scripts, experiments, and tests
├── src/                # Main application source code
│   ├── app.py          # Application entry point
│   ├── main.py         # Main loop/initialization
│   ├── communication/  # MQTT and WiFi managers
│   ├── control/        # Device state, error handling, lifecycle
│   ├── sensors/        # Sensor drivers and management
│   └── utils/          # Utilities (config, logging, etc.)
└── README.md           # Project documentation
```

## Example Use Cases

- **Environmental Monitoring**: Collect data from gas, temperature, and humidity sensors and publish via MQTT
- **Remote Device Control**: Manage actuators or relays based on sensor input and remote commands
- **Educational Projects**: Use as a base for coursework or prototyping new IoT ideas

## Key Concepts Demonstrated

- **Object-Oriented Design**: Sensor and device abstraction
- **Event-Driven Programming**: State and lifecycle management
- **Configuration Management**: JSON-based config for easy deployment
- **Network Communication**: MQTT and WiFi integration

## Technology Stack

- **Language**: MicroPython / Python 3 (for Pico)
- **Hardware**: Raspberry Pi Pico (or compatible)
- **Protocols**: MQTT, WiFi

## Getting Started

### Prerequisites

- Raspberry Pi Pico (or compatible board)
- MicroPython firmware installed
- MQTT broker (e.g., Mosquitto)
- WiFi network credentials

### Setup & Running

1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd generic-pico-sw
   ```
2. Edit `config/config.json` with your WiFi and MQTT settings.
3. Copy the contents to your Pico (using Thonny, ampy, or similar tools).
4. Run `src/main.py` or `src/app.py` as your entry point.

### Example: Running on Pico

- Open `src/main.py` in Thonny and click Run.
- Monitor output via serial console.

## Customization

- Add new sensors in `src/sensors/` and register them in `sensor_manager.py`.
- Implement custom logic in `src/app.py` or create new scripts in `my/`.
- Adjust configuration in `config/config.json`.

## License

This repository is licensed under the MIT License. You are free to use, modify, and distribute the code for educational and non-commercial purposes. See the [LICENSE](LICENSE) file for details. 

---