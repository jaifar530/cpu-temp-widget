"""
System tray icon and menu for CPU Temperature Widget.
"""

import os
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from config import get_config


class SystemTray(QSystemTrayIcon):
    """
    System tray icon with context menu.
    
    Features:
    - Left-click: Toggle widget visibility
    - Right-click: Context menu with settings access
    - Dynamic icon updates (optional: show temperature in icon)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        self._current_temp = 0.0
        self._is_warning = False
        
        self._setup_icon()
        self._setup_menu()
        self._setup_connections()
        
        self.setToolTip("CPU Temperature Widget")
    
    def _setup_icon(self):
        """Set up the tray icon."""
        icon = self._create_temp_icon()
        self.setIcon(icon)
    
    def _create_temp_icon(self, temperature: float = None, is_warning: bool = False) -> QIcon:
        """
        Create a tray icon, optionally showing temperature.
        
        Args:
            temperature: Optional temperature to display on icon
            is_warning: Whether to use warning colors
        """
        # Create a 32x32 pixmap
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background circle
        bg_color = QColor(255, 90, 90) if is_warning else QColor(80, 160, 255)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, size - 4, size - 4)
        
        # Draw temperature or thermometer icon
        painter.setPen(QColor(255, 255, 255))
        
        if temperature is not None and temperature >= 0:
            # Show temperature number
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font)
            
            temp_text = f"{int(temperature)}"
            rect = pixmap.rect()
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, temp_text)
        else:
            # Draw simple thermometer icon
            # Thermometer body
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRoundedRect(13, 4, 6, 18, 3, 3)
            # Thermometer bulb
            painter.drawEllipse(11, 20, 10, 10)
            # Mercury
            painter.setBrush(QColor(255, 90, 90))
            painter.drawRoundedRect(14, 10, 4, 12, 2, 2)
            painter.drawEllipse(12, 21, 8, 8)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _setup_menu(self):
        """Set up the context menu."""
        self._menu = QMenu()
        
        # Show/Hide Widget
        self._show_action = QAction("Show Widget", self._menu)
        self._show_action.setCheckable(True)
        self._show_action.setChecked(self._config.widget_visible)
        self._menu.addAction(self._show_action)
        
        self._menu.addSeparator()
        
        # Settings
        self._settings_action = QAction("Settings...", self._menu)
        self._menu.addAction(self._settings_action)
        
        self._menu.addSeparator()
        
        # Start with Windows
        self._startup_action = QAction("Start with Windows", self._menu)
        self._startup_action.setCheckable(True)
        self._startup_action.setChecked(self._config.start_with_windows)
        self._startup_action.triggered.connect(self._toggle_startup)
        self._menu.addAction(self._startup_action)
        
        self._menu.addSeparator()
        
        # Exit
        self._exit_action = QAction("Exit", self._menu)
        self._exit_action.triggered.connect(self._quit_application)
        self._menu.addAction(self._exit_action)
        
        # Apply dark style
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #45475a;
            }
            QMenu::separator {
                height: 1px;
                background-color: #45475a;
                margin: 4px 8px;
            }
            QMenu::indicator:checked {
                image: none;
                background-color: #89b4fa;
                border-radius: 2px;
                width: 12px;
                height: 12px;
                margin-left: 6px;
            }
            QMenu::indicator:unchecked {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 2px;
                width: 10px;
                height: 10px;
                margin-left: 6px;
            }
        """)
        
        self.setContextMenu(self._menu)
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.activated.connect(self._on_activated)
    
    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - toggle widget
            self._toggle_widget()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # Right click - handled by context menu
            pass
    
    def _toggle_widget(self):
        """Toggle widget visibility."""
        is_checked = not self._show_action.isChecked()
        self._show_action.setChecked(is_checked)
        self._config.widget_visible = is_checked
        # Emit signal to parent to handle actual visibility
        self._show_action.triggered.emit(is_checked)
    
    def _toggle_startup(self, checked: bool):
        """Toggle start with Windows setting."""
        self._config.start_with_windows = checked
    
    def _quit_application(self):
        """Quit the application cleanly."""
        # Save config before quitting
        self._config.save()
        QApplication.quit()
    
    # Public methods
    def update_temperature(self, temperature: float, is_warning: bool = False):
        """
        Update the tray icon to reflect current temperature.
        
        Args:
            temperature: Current CPU temperature (-1 for error)
            is_warning: Whether temperature is in warning state
        """
        self._current_temp = temperature
        self._is_warning = is_warning
        
        # Update icon
        icon = self._create_temp_icon(temperature if temperature >= 0 else None, is_warning)
        self.setIcon(icon)
        
        # Update tooltip
        if temperature >= 0:
            tooltip = f"CPU Temperature: {temperature:.0f}°C"
            if is_warning:
                tooltip += " (High!)"
        else:
            tooltip = "CPU Temperature: Unable to read"
        
        self.setToolTip(tooltip)
    
    def sync_visibility_state(self, is_visible: bool):
        """Sync the show/hide action state with actual widget visibility."""
        self._show_action.setChecked(is_visible)
    
    def sync_startup_state(self):
        """Sync the startup action with the actual registry state."""
        actual_state = self._config.check_startup_registry()
        self._startup_action.setChecked(actual_state)
        if actual_state != self._config.start_with_windows:
            self._config.set('start_with_windows', actual_state, auto_save=False)
    
    def connect_show_action(self, callback):
        """Connect the show/hide action to a callback."""
        self._show_action.triggered.connect(callback)
    
    def connect_settings_action(self, callback):
        """Connect the settings action to a callback."""
        self._settings_action.triggered.connect(callback)
    
    def show_notification(self, title: str, message: str, icon_type=None):
        """
        Show a system notification.
        
        Args:
            title: Notification title
            message: Notification message
            icon_type: Optional icon type (Information, Warning, Critical)
        """
        if icon_type is None:
            icon_type = QSystemTrayIcon.MessageIcon.Information
        
        self.showMessage(title, message, icon_type, 5000)
