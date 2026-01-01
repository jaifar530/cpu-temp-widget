"""
Temperature monitoring thread for CPU Temperature Widget.
Uses multiple methods to read CPU temperature:
1. LibreHardwareMonitor WMI (if LHM is running)
2. OpenHardwareMonitor WMI (if OHM is running)
3. WMI Thermal Zone (built-in Windows, requires admin)
4. Simulation (fallback for demo/testing)
"""

import ctypes
import os
import sys
import random
import time
from pathlib import Path
from typing import Optional, List, Tuple

from PyQt6.QtCore import QThread, pyqtSignal, QMutex


def is_admin() -> bool:
    """Check if the application is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class TemperatureMonitor(QThread):
    """
    Background thread that monitors CPU temperature.
    
    Signals:
        temperature_updated(float): Emitted when temperature is read. -1 means error.
        error_occurred(str): Emitted when an error occurs (only once per session).
    """
    
    temperature_updated = pyqtSignal(float)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, update_interval: float = 1.0):
        super().__init__()
        self._interval = update_interval
        self._running = False
        self._mutex = QMutex()
        self._wmi_lhm = None
        self._wmi_ohm = None
        self._wmi_thermal = None
        self._method = "none"
        self._error_shown = False
        self._last_real_temp = None
    
    def set_interval(self, interval: float):
        """Set the update interval in seconds."""
        self._mutex.lock()
        self._interval = interval
        self._mutex.unlock()
    
    def _init_libre_hardware_monitor_wmi(self) -> bool:
        """
        Initialize WMI connection to LibreHardwareMonitor.
        LHM must be running for this to work.
        """
        try:
            import wmi
            self._wmi_lhm = wmi.WMI(namespace="root/LibreHardwareMonitor")
            
            # Test if we can read sensors
            sensors = self._wmi_lhm.Sensor()
            for sensor in sensors:
                if sensor.SensorType == "Temperature":
                    self._method = "LibreHardwareMonitor"
                    return True
            
            # Namespace exists but no temperature sensors yet
            if sensors:
                self._method = "LibreHardwareMonitor"
                return True
                
        except Exception as e:
            self._wmi_lhm = None
        
        return False
    
    def _init_open_hardware_monitor_wmi(self) -> bool:
        """
        Initialize WMI connection to OpenHardwareMonitor.
        OHM must be running for this to work.
        """
        try:
            import wmi
            self._wmi_ohm = wmi.WMI(namespace="root/OpenHardwareMonitor")
            
            sensors = self._wmi_ohm.Sensor()
            for sensor in sensors:
                if sensor.SensorType == "Temperature":
                    self._method = "OpenHardwareMonitor"
                    return True
            
            if sensors:
                self._method = "OpenHardwareMonitor"
                return True
                
        except Exception as e:
            self._wmi_ohm = None
        
        return False
    
    def _init_wmi_thermal(self) -> bool:
        """Initialize WMI thermal zone (requires admin on most systems)."""
        try:
            import wmi
            self._wmi_thermal = wmi.WMI(namespace="root/wmi")
            
            temps = self._wmi_thermal.MSAcpi_ThermalZoneTemperature()
            if temps and temps[0].CurrentTemperature > 0:
                temp_kelvin = temps[0].CurrentTemperature / 10.0
                temp_celsius = temp_kelvin - 273.15
                if 0 < temp_celsius < 150:
                    self._method = "WMI-ThermalZone"
                    return True
                    
        except Exception:
            self._wmi_thermal = None
        
        return False
    
    def _get_temp_from_lhm(self) -> Optional[float]:
        """Get CPU temperature from LibreHardwareMonitor WMI."""
        if not self._wmi_lhm:
            return None
        
        try:
            sensors = self._wmi_lhm.Sensor()
            
            cpu_package_temp = None
            cpu_core_temps = []
            cpu_max_temp = None
            cpu_avg_temp = None
            
            for sensor in sensors:
                if sensor.SensorType == "Temperature" and sensor.Value is not None:
                    name = sensor.Name.lower() if sensor.Name else ""
                    parent = sensor.Parent.lower() if sensor.Parent else ""
                    
                    # Check if it's a CPU sensor
                    is_cpu = "cpu" in parent or "intel" in parent or "amd" in parent or "processor" in parent
                    
                    if is_cpu or "cpu" in name or "core" in name:
                        value = float(sensor.Value)
                        
                        if value <= 0 or value > 150:
                            continue
                        
                        # Prioritize different sensor types
                        if "package" in name:
                            cpu_package_temp = value
                        elif "max" in name:
                            cpu_max_temp = value
                        elif "average" in name:
                            cpu_avg_temp = value
                        elif "core" in name:
                            cpu_core_temps.append(value)
            
            # Return in order of preference
            if cpu_package_temp is not None:
                return cpu_package_temp
            if cpu_avg_temp is not None:
                return cpu_avg_temp
            if cpu_max_temp is not None:
                return cpu_max_temp
            if cpu_core_temps:
                return sum(cpu_core_temps) / len(cpu_core_temps)
            
        except Exception:
            pass
        
        return None
    
    def _get_temp_from_ohm(self) -> Optional[float]:
        """Get CPU temperature from OpenHardwareMonitor WMI."""
        if not self._wmi_ohm:
            return None
        
        try:
            sensors = self._wmi_ohm.Sensor()
            
            cpu_package_temp = None
            cpu_core_temps = []
            
            for sensor in sensors:
                if sensor.SensorType == "Temperature" and sensor.Value is not None:
                    name = sensor.Name.lower() if sensor.Name else ""
                    value = float(sensor.Value)
                    
                    if value <= 0 or value > 150:
                        continue
                    
                    if "cpu" in name or "core" in name:
                        if "package" in name:
                            cpu_package_temp = value
                        else:
                            cpu_core_temps.append(value)
            
            if cpu_package_temp is not None:
                return cpu_package_temp
            if cpu_core_temps:
                return sum(cpu_core_temps) / len(cpu_core_temps)
            
        except Exception:
            pass
        
        return None
    
    def _get_temp_from_thermal(self) -> Optional[float]:
        """Get temperature from WMI thermal zone."""
        if not self._wmi_thermal:
            return None
        
        try:
            temps = self._wmi_thermal.MSAcpi_ThermalZoneTemperature()
            if temps and temps[0].CurrentTemperature > 0:
                temp_kelvin = temps[0].CurrentTemperature / 10.0
                temp_celsius = temp_kelvin - 273.15
                if 0 < temp_celsius < 150:
                    return temp_celsius
        except Exception:
            pass
        
        return None
    
    def _get_simulated_temp(self) -> float:
        """Generate simulated temperature for demo."""
        base = 48.0
        slow_wave = 8.0 * (0.5 + 0.5 * (time.time() % 60) / 60)
        noise = random.uniform(-1.5, 1.5)
        spike = random.uniform(5, 10) if random.random() < 0.05 else 0
        return round(base + slow_wave + noise + spike, 1)
    
    def get_temperature(self) -> Tuple[Optional[float], str]:
        """
        Get the current CPU temperature.
        Returns: (temperature, source) where source indicates where the reading came from.
        """
        # Try LibreHardwareMonitor first
        temp = self._get_temp_from_lhm()
        if temp is not None:
            self._last_real_temp = temp
            return temp, "LHM"
        
        # Try OpenHardwareMonitor
        temp = self._get_temp_from_ohm()
        if temp is not None:
            self._last_real_temp = temp
            return temp, "OHM"
        
        # Try WMI Thermal Zone
        temp = self._get_temp_from_thermal()
        if temp is not None:
            self._last_real_temp = temp
            return temp, "WMI"
        
        # Fall back to simulation
        return self._get_simulated_temp(), "SIM"
    
    def get_method(self) -> str:
        """Get the current temperature reading method."""
        return self._method
    
    def run(self):
        """Main monitoring loop."""
        self._running = True
        
        # Try to initialize temperature sources
        lhm_ok = self._init_libre_hardware_monitor_wmi()
        ohm_ok = self._init_open_hardware_monitor_wmi() if not lhm_ok else False
        thermal_ok = self._init_wmi_thermal() if not (lhm_ok or ohm_ok) else False
        
        if not (lhm_ok or ohm_ok or thermal_ok):
            self._method = "Simulation"
            if not self._error_shown:
                self._error_shown = True
                self.error_occurred.emit(
                    "Using simulated temperature.\n"
                    "For real readings, run LibreHardwareMonitor."
                )
        
        while self._running:
            self._mutex.lock()
            interval = self._interval
            self._mutex.unlock()
            
            temp, source = self.get_temperature()
            
            # Re-check for LHM/OHM if we're using simulation (they might have started)
            if source == "SIM" and not self._error_shown:
                if self._init_libre_hardware_monitor_wmi():
                    source = "LHM"
                    temp, _ = self.get_temperature()
                elif self._init_open_hardware_monitor_wmi():
                    source = "OHM"
                    temp, _ = self.get_temperature()
            
            if temp is not None:
                self.temperature_updated.emit(temp)
            else:
                self.temperature_updated.emit(-1)
            
            self.msleep(int(interval * 1000))
    
    def stop(self):
        """Stop the monitoring thread."""
        self._running = False
        self.wait(2000)


class WarningStateTracker:
    """
    Tracks the warning state to determine when to show HOT indicator.
    Shows HOT indicator after temperature is above threshold for 5+ seconds.
    """
    
    def __init__(self, threshold: int = 70, hot_delay: float = 5.0):
        self._threshold = threshold
        self._hot_delay = hot_delay
        self._above_threshold_since: Optional[float] = None
    
    def update_threshold(self, threshold: int):
        """Update the warning threshold."""
        self._threshold = threshold
        self._above_threshold_since = None
    
    def update(self, temperature: float) -> Tuple[bool, bool]:
        """
        Update the warning state with a new temperature reading.
        
        Returns:
            (is_warning, show_hot): Tuple of warning state and hot indicator state.
        """
        is_warning = temperature >= self._threshold
        show_hot = False
        
        if is_warning:
            if self._above_threshold_since is None:
                self._above_threshold_since = time.time()
            elif time.time() - self._above_threshold_since >= self._hot_delay:
                show_hot = True
        else:
            self._above_threshold_since = None
        
        return is_warning, show_hot
