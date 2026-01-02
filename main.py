"""
CPU Temperature Widget - Main Application Entry Point

A polished Windows desktop widget that displays CPU temperature
with a translucent overlay and system tray integration.

Author: Virtual Platforms LLC
"""

import sys
import os

# Ensure the application directory is in the path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, APP_DIR)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QIcon

from config import get_config
from widget import TemperatureWidget
from tray import SystemTray
from settings_dialog import SettingsDialog
from temp_monitor import TemperatureMonitor, WarningStateTracker, is_admin


class CPUTempWidgetApp:
    """
    Main application controller.
    
    Coordinates the widget, system tray, settings dialog,
    and temperature monitoring components.
    """
    
    def __init__(self):
        self._config = get_config()
        self._settings_dialog = None
        
        # Create components
        self._widget = TemperatureWidget()
        self._tray = SystemTray()
        self._warning_tracker = WarningStateTracker(
            threshold=self._config.warning_threshold
        )
        self._monitor = TemperatureMonitor(
            update_interval=self._config.update_interval
        )
        
        # Connect signals
        self._setup_connections()
        
        # Show admin warning on first run if not admin
        if self._config.first_run:
            self._config.first_run = False
            if not is_admin():
                QTimer.singleShot(2000, self._show_admin_notification)
    
    def _setup_connections(self):
        """Set up signal connections between components."""
        # Temperature updates
        self._monitor.temperature_updated.connect(self._on_temperature_updated)
        self._monitor.error_occurred.connect(self._on_monitor_error)
        
        # Tray actions
        self._tray.connect_show_action(self._toggle_widget_visibility)
        self._tray.connect_settings_action(self._show_settings)
        
        # Widget actions
        self._widget.connect_settings_action(self._show_settings)
    
    def _on_temperature_updated(self, temperature: float):
        """Handle temperature update from monitor."""
        # Update widget
        self._widget.update_temperature(temperature)
        
        # Update warning state
        is_warning, show_hot = self._warning_tracker.update(temperature)
        self._widget.set_warning_state(is_warning, show_hot)
        
        # Update tray
        self._tray.update_temperature(temperature, is_warning)
    
    def _on_monitor_error(self, error: str):
        """Handle error from temperature monitor."""
        # Show as tray notification instead of console
        self._tray.show_notification(
            "CPU Temperature Widget",
            error,
            self._tray.MessageIcon.Warning
        )
    
    def _toggle_widget_visibility(self, visible: bool):
        """Toggle widget visibility."""
        if visible:
            self._widget.show()
        else:
            self._widget.hide()
        
        self._config.widget_visible = visible
        self._tray.sync_visibility_state(visible)
    
    def _show_settings(self):
        """Show the settings dialog."""
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog()
            self._settings_dialog.settings_changed.connect(self._apply_settings)
            self._settings_dialog.position_reset.connect(self._reset_position)
        
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()
    
    def _apply_settings(self):
        """Apply changed settings to all components."""
        # Update monitor interval
        self._monitor.set_interval(self._config.update_interval)
        
        # Update warning tracker threshold
        self._warning_tracker.update_threshold(self._config.warning_threshold)
        
        # Update widget appearance
        self._widget.apply_settings()
        
        # Sync tray startup state
        self._tray.sync_startup_state()
    
    def _reset_position(self):
        """Reset widget position."""
        self._widget.reset_position()
    
    def _show_admin_notification(self):
        """Show notification about administrator privileges."""
        self._tray.show_notification(
            "CPU Temperature Widget",
            "For accurate CPU temperature readings, run as Administrator.\n"
            "The widget will still work but may show simulated values.",
            self._tray.MessageIcon.Warning
        )
    
    def start(self):
        """Start the application."""
        # Show tray icon
        self._tray.show()
        
        # Show widget if configured
        if self._config.widget_visible:
            self._widget.show()
        
        # Start temperature monitoring
        self._monitor.start()
    
    def stop(self):
        """Stop the application and clean up."""
        # Stop monitoring
        self._monitor.stop()
        
        # Save config
        self._config.save()
        
        # Hide components
        self._tray.hide()
        self._widget.hide()


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    # Set application info
    app.setApplicationName("CPU Temperature Widget")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("Virtual Platforms LLC")
    
    # Set application icon globally
    icon_path = os.path.join(APP_DIR, 'resources', 'icon.ico')
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - check MEIPASS
        icon_path = os.path.join(sys._MEIPASS, 'resources', 'icon.ico')
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and start the application controller
    cpu_widget = CPUTempWidgetApp()
    cpu_widget.start()
    
    # Handle application quit
    app.aboutToQuit.connect(cpu_widget.stop)
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
