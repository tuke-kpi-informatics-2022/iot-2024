import json
import os
from src.control.device_state import DeviceState
from src.defaults import DEFAULT_POST_GLOBAL_ERROR, DEFAULT_TRANSITION_TO_ERROR_STATE, AUTO_RESTART_ON_ERROR, DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_DEFAULT_PATH, DEFAULT_ENABLE_FACTORY_RESET

class SystemManager:
    def __init__(self, config, mqtt_manager, power, logger, error_handler):
        """
        SystemManager is responsible for handling system level commands and configurations.

        Args:
            config (dict): The system configuration.
            mqtt_manager (MqttManager): The MQTT manager object.
            power (PowerManager): The power manager object.
            logger (Logger): The logger object.
            error_handler (function): The error handler function.
        """
        
        self.mqtt_manager = mqtt_manager
        self.logger = logger
        self.error_handler = error_handler
        self.power = power
        self.config = config
        self.system_config = config.get_system_config()
        self.subscribe_cfg = self.system_config.get("mqtt", {}).get("subscribe", {})
        self.enable_factory_reset = self.system_config.get("enable_factory_reset", True)
        self.logger.log_info("Initialize System Manager....")

    def initialize(self):
        """
        initialize the system manager.
        Subscribe to system commands and power config topics.
        """

        cmds_topic = self.subscribe_cfg.get("commands", None)
        p_cfg_topic = self.subscribe_cfg.get("power_config", None)

        if cmds_topic is not None:
            self.logger.log_info(f"SystemManager: subscribing to {cmds_topic}")
            self.mqtt_manager.subscribe(cmds_topic, self._make_cb)
        else:
            self.logger.log_warning("SystemManager: No system commands topic found.")

        if p_cfg_topic is not None:
            self.logger.log_info(f"SystemManager: subscribing to power config {p_cfg_topic}")
            self.mqtt_manager.subscribe(p_cfg_topic, self._make_cb)
        else:
            self.logger.log_warning("SystemManager: No power config topic found.")


    def _make_cb(self, topic, msg):
        """
        Unified callback to handle system commands and power config updates.
        """
        try:
            self.logger.log_info(f"Message received(topic: {topic}, msg: {msg})")
            parsed_msg = json.loads(msg.decode("utf-8"))

           # Determine action based on topic
            if "commands" in topic:
                command = parsed_msg.get("command")

                if command == "factory_reset" and self.system_config.get("enable_factory_reset", DEFAULT_ENABLE_FACTORY_RESET):
                    self.logger.log_info("Handling factory reset command.")
                    self.config.reset_config()

                    self.logger.log_info("Rebooting after factory reset.")
                    self.power.reboot()
                elif command == "shutdown":
                    self.power.shutdown()
                elif command == "reboot":
                    self.power.reboot()
                else:
                    self.logger.log_warning(f"Unknown or disabled system command: {command}")

            elif "power_config" in topic:
                ds = parsed_msg.get("deep_sleep_interval_s")
                wdt = parsed_msg.get("watchdog_timeout")

                self.logger.log_info(f"Updating power config: ds={ds}, wdt={wdt}")

                changed = False

                if ds is not None:
                    self.system_config["deep_sleep_interval_s"] = ds
                    changed = True
                if wdt is not None:
                    self.system_config["watchdog_timeout"] = wdt
                    changed = True
                
                if changed:
                    self.config.save_config()


        except Exception as e:
            self.logger.log_error(f"Message parse error: {e}")
            self.error_handler(f"Message parse error: {e}")