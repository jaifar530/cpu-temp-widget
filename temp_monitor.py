"""
Temperature monitoring thread for CPU Temperature Widget.
Uses multiple methods to read CPU temperature:
1. LibreHardwareMonitor (most accurate, requires admin + pythonnet)
2. WMI (Windows built-in, limited support)
3. Simulation (fallback for demo/testing)
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
        error_occurred(str): Emitted when an error occurs.
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
        self._wmi = None
        self._method = "none"  # Track which method is being used
    
    def set_interval(self, interval: float):
        """Set the update interval in seconds."""
        self._mutex.lock()
        self._interval = interval
        self._mutex.unlock()
    
    def _init_libre_hardware_monitor(self) -> bool:
        """Initialize LibreHardwareMonitor."""
        try:
            import clr
            
            # Try to find LibreHardwareMonitorLib.dll
            dll_paths = [
                # Same directory as script/executable
                Path(sys.executable).parent / 'LibreHardwareMonitorLib.dll',
                Path(__file__).parent / 'LibreHardwareMonitorLib.dll',
                Path(__file__).parent / 'resources' / 'LibreHardwareMonitorLib.dll',
                # Current working directory
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
                # Try without explicit path (must be in PATH or GAC)
                clr.AddReference('LibreHardwareMonitorLib')
            
            from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType
            
            self._computer = Computer()
            self._computer.IsCpuEnabled = True
            self._computer.Open()
            
            self._HardwareType = HardwareType
            self._SensorType = SensorType
            self._lhm_initialized = True
            self._method = "LibreHardwareMonitor"
            return True
            
        except ImportError:
            # pythonnet not installed
            return False
        except Exception as e:
            self.error_occurred.emit(f"LibreHardwareMonitor init failed: {e}")
            return False
    
    def _init_wmi(self) -> bool:
        """Initialize WMI for temperature reading."""
        try:
            import wmi
            # Try thermal zone temperature
            self._wmi = wmi.WMI(namespace="root\\wmi")
            # Test if we can read temperature
            try:
                temps = self._wmi.MSAcpi_ThermalZoneTemperature()
                if temps:
                    self._wmi_initialized = True
                    self._method = "WMI"
                    return True
            except Exception:
                pass
            
            # Try OpenHardwareMonitor WMI namespace (if OHM is running)
            try:
                self._wmi = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = self._wmi.Sensor()
                if sensors:
                    self._wmi_initialized = True
                    self._method = "WMI-OHM"
                    return True
            except Exception:
                pass
            
            return False
            
        except ImportError:
            # wmi module not installed, try to install it
            return False
        except Exception as e:
            self.error_occurred.emit(f"WMI init failed: {e}")
            return False
    
    def _get_cpu_temp_lhm(self) -> Optional[float]:
        """Get CPU temperature using LibreHardwareMonitor."""
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
                                if 'package' in name or 'cpu' in name:
                                    package_temp = float(sensor.Value)
                                temps.append(float(sensor.Value))
                    
                    # Also check sub-hardware
                    for sub in hardware.SubHardware:
                        sub.Update()
                        for sensor in sub.Sensors:
                            if sensor.SensorType == self._SensorType.Temperature:
                                if sensor.Value is not None:
                                    temps.append(float(sensor.Value))
            
            # Prefer package temp, otherwise average
            if package_temp is not None:
                return package_temp
            elif temps:
                return sum(temps) / len(temps)
            
            return None
            
        except Exception as e:
            self.error_occurred.emit(f"LHM read error: {e}")
            return None
    
    def _get_cpu_temp_wmi(self) -> Optional[float]:
        """Get CPU temperature using WMI."""
        if not self._wmi_initialized or not self._wmi:
            return None
        
        try:
            if self._method == "WMI-OHM":
                # OpenHardwareMonitor WMI
                sensors = self._wmi.Sensor()
                for sensor in sensors:
                    if "temperature" in sensor.SensorType.lower() and "cpu" in sensor.Name.lower():
                        return float(sensor.Value)
            else:
                # Standard thermal zone
                temps = self._wmi.MSAcpi_ThermalZoneTemperature()
                if temps:
                    # Temperature is in tenths of Kelvin
                    temp_kelvin = temps[0].CurrentTemperature / 10.0
                    temp_celsius = temp_kelvin - 273.15
                    if 0 < temp_celsius < 150:  # Sanity check
                        return temp_celsius
        except Exception:
            pass
        
        return None
    
    def _get_cpu_temp_simulation(self) -> float:
        """
        Simulated temperature for testing/demo purposes.
        Returns a temperature that varies realistically.
        """
        # Base temperature around 45-55°C with some variation based on time
        base = 48.0
        
        # Add slow oscillation (simulates load changes)
        slow_wave = 8.0 * (0.5 + 0.5 * (time.time() % 60) / 60)
        
        # Add small random noise
        noise = random.uniform(-1.5, 1.5)
        
        # Occasional "spikes" (10% chance of +5-10°C)
        spike = 0
        if random.random() < 0.1:
            spike = random.uniform(5, 10)
        
        return round(base + slow_wave + noise + spike, 1)
    
    def get_temperature(self) -> Optional[float]:
        """Get the current CPU temperature."""
        # Try LibreHardwareMonitor first
        temp = self._get_cpu_temp_lhm()
        if temp is not None:
            return temp
        
        # Try WMI fallback
        temp = self._get_cpu_temp_wmi()
        if temp is not None:
            return temp
        
        # Use simulation as last resort (for demo/testing)
        return self._get_cpu_temp_simulation()
    
    def get_method(self) -> str:
        """Get the current temperature reading method."""
        return self._method
    
    def run(self):
        """Main monitoring loop."""
        self._running = True
        
        # Try to initialize temperature reading methods
        lhm_ok = self._init_libre_hardware_monitor()
        
        if not lhm_ok:
            wmi_ok = self._init_wmi()
            
            if not wmi_ok:
                self._method = "Simulation"
                if not is_admin():
                    self.error_occurred.emit(
                        "Running without admin privileges. Using simulated temperature. "
                        "Run as Administrator for real CPU temperature readings."
                    )
                else:
                    self.error_occurred.emit(
                        "Could not initialize temperature monitoring. Using simulated values. "
                        "Install pythonnet and LibreHardwareMonitor for accurate readings."
                    )
        
        while self._running:
            self._mutex.lock()
            interval = self._interval
            self._mutex.unlock()
            
            temp = self.get_temperature()
            
            if temp is not None:
                self.temperature_updated.emit(temp)
            else:
                self.temperature_updated.emit(-1)  # Signal error
            
            # Sleep for the interval (in milliseconds)
            self.msleep(int(interval * 1000))
    
    def stop(self):
        """Stop the monitoring thread."""
        self._running = False
        
        # Clean up LibreHardwareMonitor
        if self._computer is not None:
            try:
                self._computer.Close()
            except Exception:
                pass
        
        self.wait(2000)  # Wait up to 2 seconds for thread to finish


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
