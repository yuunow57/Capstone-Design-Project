from PyQt_Service.Setting import (
    USBPortManager,
    ChargeLimitManager,
    SensorResetManager,
    VoltageThresholdManager,
    ReconnectManager,
    ConfigApplyManager
)

class SettingController:
    def __init__(self, ui):
        self.ui = ui
        self.usb_manager = USBPortManager(self.ui)
        self.charge_manager = ChargeLimitManager(self.ui)
        self.sensor_reset_manager = SensorResetManager(self.ui)
        self.voltage_manager = VoltageThresholdManager(self.ui)
        self.reconnect_manager = ReconnectManager(self.ui, port=self.usb_manager.selected_port)        
        self.config_manager = ConfigApplyManager(self.ui)