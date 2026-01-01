"""
Configuration management for CPU Temperature Widget.
Stores settings in %APPDATA%/CPUTempWidget/config.json
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
import winreg


class Config:
    """Manages application configuration with auto-save functionality."""
    
    # Default configuration values
    DEFAULTS = {
        # Widget position (None means center of primary screen)
        'position_x': None,
        'position_y': None,
        'position_locked': False,
        
        # Appearance
        'warning_threshold': 70,  # °C
        'text_size': 'medium',    # small, medium, large
        'transparency': 60,       # percent (30-90)
        'always_on_top': True,
        
        # Behavior
        'update_interval': 1.0,   # seconds (0.5, 1.0, 2.0)
        'start_with_windows': False,
        'widget_visible': True,
        
        # Internal
        'first_run': True,
    }
    
    # Text size mappings (font size in points)
    TEXT_SIZES = {
        'small': 14,
        'medium': 18,
        'large': 24,
    }
    
    # Update interval options
    UPDATE_INTERVALS = [0.5, 1.0, 2.0]
    
    def __init__(self):
        """Initialize configuration manager."""
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / 'config.json'
        self._settings = dict(self.DEFAULTS)
        self._load()
    
    def _get_config_dir(self) -> Path:
        """Get the configuration directory path."""
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            config_dir = Path(appdata) / 'CPUTempWidget'
        else:
            # Fallback to user home
            config_dir = Path.home() / '.cpu_temp_widget'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def _load(self):
        """Load configuration from file."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults (in case new settings were added)
                    for key, value in loaded.items():
                        if key in self.DEFAULTS:
                            self._settings[key] = value
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config: {e}")
                # Use defaults on error
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True):
        """Set a configuration value."""
        if key in self.DEFAULTS:
            self._settings[key] = value
            if auto_save:
                self.save()
    
    def reset_position(self):
        """Reset widget position to default (center of screen)."""
        self._settings['position_x'] = None
        self._settings['position_y'] = None
        self.save()
    
    # Convenience properties
    @property
    def position(self) -> tuple[Optional[int], Optional[int]]:
        """Get widget position as (x, y) tuple."""
        return (self._settings['position_x'], self._settings['position_y'])
    
    @position.setter
    def position(self, pos: tuple[int, int]):
        """Set widget position."""
        self._settings['position_x'] = pos[0]
        self._settings['position_y'] = pos[1]
        self.save()
    
    @property
    def position_locked(self) -> bool:
        return self._settings['position_locked']
    
    @position_locked.setter
    def position_locked(self, value: bool):
        self._settings['position_locked'] = value
        self.save()
    
    @property
    def warning_threshold(self) -> int:
        return self._settings['warning_threshold']
    
    @warning_threshold.setter
    def warning_threshold(self, value: int):
        self._settings['warning_threshold'] = max(40, min(100, value))
        self.save()
    
    @property
    def text_size(self) -> str:
        return self._settings['text_size']
    
    @text_size.setter
    def text_size(self, value: str):
        if value in self.TEXT_SIZES:
            self._settings['text_size'] = value
            self.save()
    
    @property
    def font_size(self) -> int:
        """Get the actual font size in points."""
        return self.TEXT_SIZES.get(self.text_size, 18)
    
    @property
    def transparency(self) -> int:
        return self._settings['transparency']
    
    @transparency.setter
    def transparency(self, value: int):
        self._settings['transparency'] = max(30, min(90, value))
        self.save()
    
    @property
    def always_on_top(self) -> bool:
        return self._settings['always_on_top']
    
    @always_on_top.setter
    def always_on_top(self, value: bool):
        self._settings['always_on_top'] = value
        self.save()
    
    @property
    def update_interval(self) -> float:
        return self._settings['update_interval']
    
    @update_interval.setter
    def update_interval(self, value: float):
        if value in self.UPDATE_INTERVALS:
            self._settings['update_interval'] = value
            self.save()
    
    @property
    def start_with_windows(self) -> bool:
        return self._settings['start_with_windows']
    
    @start_with_windows.setter
    def start_with_windows(self, value: bool):
        self._settings['start_with_windows'] = value
        self._update_startup_registry(value)
        self.save()
    
    @property
    def widget_visible(self) -> bool:
        return self._settings['widget_visible']
    
    @widget_visible.setter
    def widget_visible(self, value: bool):
        self._settings['widget_visible'] = value
        self.save()
    
    @property
    def first_run(self) -> bool:
        return self._settings['first_run']
    
    @first_run.setter
    def first_run(self, value: bool):
        self._settings['first_run'] = value
        self.save()
    
    def _update_startup_registry(self, enable: bool):
        """Add or remove the app from Windows startup."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "CPUTempWidget"
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
            )
            
            if enable:
                # Get the executable path
                import sys
                exe_path = sys.executable
                if hasattr(sys, 'frozen'):
                    # Running as compiled exe
                    exe_path = sys.executable
                else:
                    # Running from Python script
                    exe_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # Already removed
            
            winreg.CloseKey(key)
        except WindowsError as e:
            print(f"Warning: Could not update startup registry: {e}")
    
    def check_startup_registry(self) -> bool:
        """Check if the app is set to start with Windows."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "CPUTempWidget"
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_QUERY_VALUE
            )
            
            try:
                winreg.QueryValueEx(key, app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except WindowsError:
            return False


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
