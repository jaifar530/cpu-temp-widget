"""
Temperature monitoring thread for CPU Temperature Widget.
Uses multiple methods to read CPU temperature:
1. OpenHardwareMonitor WMI (if OHM/LHM is running)
2. LibreHardwareMonitor DLL (requires admin + pythonnet)
3. WMI Thermal Zone (built-in Windows, limited support)
4. Simulation (fallback for demo/testing)
"""

import ctypes
import os
import sys
import random
import time
from pathlib import Path
from typing import Optional

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
        self._computer = None
        self._lhm_initialized = False
        self._wmi_initialized = False
        self._wmi_ohm_initialized = False
        self._wmi = None
        self._wmi_ohm = None
        self._method = "none"
        self._error_shown = False
    
    def set_interval(self, interval: float):
        """Set the update interval in seconds."""
        self._mutex.lock()
        self._interval = interval
        self._mutex.unlock()
    
    def _init_wmi_ohm(self) -> bool:
        """
        Initialize WMI connection to OpenHardwareMonitor/LibreHardwareMonitor.
        This works if OHM or LHM is running in the background (no admin needed for our app).
        """
        try:
            import wmi
            # Try OpenHardwareMonitor WMI namespace
            self._wmi_ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            sensors = self._wmi_ohm.Sensor()
            
            # Check if we can find CPU temperature sensors
            for sensor in sensors:
                if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                    self._wmi_ohm_initialized = True
                    self._method = "OpenHardwareMonitor"
                    return True
            
            # Even if no CPU sensor yet, the namespace exists
            if sensors:
                self._wmi_ohm_initialized = True
                self._method = "OpenHardwareMonitor"
                return True
                
        except Exception:
            pass
        
        try:
            import wmi
            # Try LibreHardwareMonitor WMI namespace
            self._wmi_ohm = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            sensors = self._wmi_ohm.Sensor()
            
            if sensors:
                self._wmi_ohm_initialized = True
                self._method = "LibreHardwareMonitor"
                return True
                
        except Exception:
            pass
        
        return False
    
    def _init_libre_hardware_monitor(self) -> bool:
        """Initialize LibreHardwareMonitor via pythonnet (requires admin)."""
        try:
            import clr
            
            dll_paths = [
                Path(sys.executable).parent / 'LibreHardwareMonitorLib.dll',
                Path(__file__).parent / 'LibreHardwareMonitorLib.dll',
                Path(__file__).parent / 'resources' / 'LibreHardwareMonitorLib.dll',
                Path.cwd() / 'LibreHardwareMonitorLib.dll',
            ]
            
            dll_found = None
            for dll_path in dll_paths:
                if dll_path.exists():
                    dll_found = str(dll_path)
                    break
            
            if dll_found:
                clr.AddReference(dll_found)
            else:
                clr.AddReference('LibreHardwareMonitorLib')
            
            from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType
            
            self._computer = Computer()
            self._computer.IsCpuEnabled = True
            self._computer.Open()
            
            self._HardwareType = HardwareType
            self._SensorType = SensorType
            self._lhm_initialized = True
            self._method = "LibreHardwareMonitor-DLL"
            return True
            
        except ImportError:
            return False
        except Exception:
            return False
    
    def _init_wmi_thermal(self) -> bool:
        """Initialize WMI thermal zone temperature (built-in Windows)."""
        try:
            import wmi
            self._wmi = wmi.WMI(namespace="root\\wmi")
            
            # Test if we can read temperature
            temps = self._wmi.MSAcpi_ThermalZoneTemperature()
            if temps and temps[0].CurrentTemperature > 0:
                temp_kelvin = temps[0].CurrentTemperature / 10.0
                temp_celsius = temp_kelvin - 273.15
                if 0 < temp_celsius < 150:
                    self._wmi_initialized = True
                    self._method = "WMI-ThermalZone"
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def _get_cpu_temp_ohm(self) -> Optional[float]:
        """Get CPU temperature from OpenHardwareMonitor/LibreHardwareMonitor WMI."""
        if not self._wmi_ohm_initialized or not self._wmi_ohm:
            return None
        
        try:
            sensors = self._wmi_ohm.Sensor()
            
            # Look for CPU Package temperature first (most accurate)
            for sensor in sensors:
                if sensor.SensorType == "Temperature":
                    name = sensor.Name.lower()
                    if "cpu package" in name or "cpu" in name and "package" in name:
                        if sensor.Value is not None and sensor.Value > 0:
                            return float(sensor.Value)
            
            # Fallback to any CPU temperature
            for sensor in sensors:
                if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                    if sensor.Value is not None and sensor.Value > 0:
                        return float(sensor.Value)
            
            # Fallback to any temperature sensor
            for sensor in sensors:
                if sensor.SensorType == "Temperature":
                    if sensor.Value is not None and sensor.Value > 0:
                        return float(sensor.Value)
                        
        except Exception:
            pass
        
        return None
    
    def _get_cpu_temp_lhm(self) -> Optional[float]:
        """Get CPU temperature using LibreHardwareMonitor DLL."""
        if not self._lhm_initialized or not self._computer:
            return None
        
        try:
            temps = []
            package_temp = None
            
            for hardware in self._computer.Hardware:
                hardware.Update()
                
                if hardware.HardwareType == self._HardwareType.Cpu:
                    for sensor in hardware.Sensors:
                        if sensor.SensorType == self._SensorType.Temperature:
                            if sensor.Value is not None:
                                name = sensor.Name.lower()
                                if 'package' in name:
                                    package_temp = float(sensor.Value)
                                temps.append(float(sensor.Value))
                    
                    for sub in hardware.SubHardware:
                        sub.Update()
                        for sensor in sub.Sensors:
                            if sensor.SensorType == self._SensorType.Temperature:
                                if sensor.Value is not None:
                                    temps.append(float(sensor.Value))
            
            if package_temp is not None:
                return package_temp
            elif temps:
                return sum(temps) / len(temps)
            
        except Exception:
            pass
        
        return None
    
    def _get_cpu_temp_wmi(self) -> Optional[float]:
        """Get CPU temperature using WMI thermal zone."""
        if not self._wmi_initialized or not self._wmi:
            return None
        
        try:
            temps = self._wmi.MSAcpi_ThermalZoneTemperature()
            if temps and temps[0].CurrentTemperature > 0:
                temp_kelvin = temps[0].CurrentTemperature / 10.0
                temp_celsius = temp_kelvin - 273.15
                if 0 < temp_celsius < 150:
                    return temp_celsius
        except Exception:
            pass
        
        return None
    
    def _get_cpu_temp_simulation(self) -> float:
        """Simulated temperature for demo purposes."""
        base = 48.0
        slow_wave = 8.0 * (0.5 + 0.5 * (time.time() % 60) / 60)
        noise = random.uniform(-1.5, 1.5)
        spike = random.uniform(5, 10) if random.random() < 0.05 else 0
        return round(base + slow_wave + noise + spike, 1)
    
    def get_temperature(self) -> Optional[float]:
        """Get the current CPU temperature using the best available method."""
        # Try OHM/LHM WMI first (works without admin if OHM is running)
        temp = self._get_cpu_temp_ohm()
        if temp is not None:
            return temp
        
        # Try LibreHardwareMonitor DLL
        temp = self._get_cpu_temp_lhm()
        if temp is not None:
            return temp
        
        # Try WMI thermal zone
        temp = self._get_cpu_temp_wmi()
        if temp is not None:
            return temp
        
        # Use simulation as last resort
        return self._get_cpu_temp_simulation()
    
    def get_method(self) -> str:
        """Get the current temperature reading method."""
        return self._method
    
    def run(self):
        """Main monitoring loop."""
        self._running = True
        
        # Try initialization methods in order of preference
        # 1. OHM/LHM WMI (no admin needed if OHM is running)
        if not self._init_wmi_ohm():
            # 2. LibreHardwareMonitor DLL (needs admin)
            if not self._init_libre_hardware_monitor():
                # 3. WMI Thermal Zone (needs admin on most systems)
                if not self._init_wmi_thermal():
                    # 4. Fall back to simulation
                    self._method = "Simulation"
                    
                    # Only show error once
                    if not self._error_shown:
                        self._error_shown = True
                        self.error_occurred.emit(
                            "Using simulated temperature. For real readings:\n"
                            "• Run OpenHardwareMonitor or HWiNFO in background, OR\n"
                            "• Run this app as Administrator"
                        )
        
        while self._running:
            self._mutex.lock()
            interval = self._interval
            self._mutex.unlock()
            
            temp = self.get_temperature()
            
            if temp is not None:
                self.temperature_updated.emit(temp)
            else:
                self.temperature_updated.emit(-1)
            
            self.msleep(int(interval * 1000))
    
    def stop(self):
        """Stop the monitoring thread."""
        self._running = False
        
        if self._computer is not None:
            try:
                self._computer.Close()
            except Exception:
                pass
        
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
    
    def update(self, temperature: float) -> tuple[bool, bool]:
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
