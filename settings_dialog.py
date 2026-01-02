"""
Settings dialog for CPU Temperature Widget.
"""

import os
import sys
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QComboBox, QSlider, QCheckBox,
    QPushButton, QGroupBox, QWidget, QSpacerItem, QSizePolicy
)

from config import get_config


class SettingsDialog(QDialog):
    """
    Settings dialog with all configurable options.
    
    Settings:
    - Warning threshold (40-100°C)
    - Text size (small/medium/large)
    - Transparency (30-90%)
    - Always on top
    - Start with Windows
    - Update interval (0.5s/1s/2s)
    - Reset position button
    """
    
    # Signal emitted when settings are applied
    settings_changed = pyqtSignal()
    position_reset = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        
        self._setup_window()
        self._setup_ui()
        self._load_values()
        self._setup_connections()
    
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("CPU Temperature Widget - Settings")
        self.setMinimumSize(380, 520)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Set window icon
        self._set_window_icon()
    
    def _set_window_icon(self):
        """Set the window icon from resources."""
        # Try to find the icon file
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, 'resources', 'icon.ico')
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def _create_group(self, title: str) -> tuple[QGroupBox, QVBoxLayout]:
        """Create a styled group box with layout."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 14px;
                padding: 8px;
                color: #cdd6f4;
                background-color: #252535;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 2px;
                padding: 0 6px;
                background-color: #1e1e2e;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)
        return group, layout
    
    def _create_row(self, label_text: str, widget: QWidget) -> QWidget:
        """Create a labeled row widget."""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)
        
        label = QLabel(label_text)
        label.setMinimumWidth(120)
        label.setStyleSheet("color: #bac2de; font-size: 12px; background: transparent;")
        
        row_layout.addWidget(label)
        row_layout.addWidget(widget, 1)
        
        return row
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main window styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QSpinBox, QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 140px;
                min-height: 20px;
                font-size: 12px;
            }
            QSpinBox:focus, QComboBox:focus {
                border-color: #89b4fa;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #45475a;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #585b70;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #cdd6f4;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #45475a;
            }
            QSlider {
                min-height: 24px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #313244;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #89b4fa;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #b4befe;
            }
            QSlider::sub-page:horizontal {
                background-color: #89b4fa;
                border-radius: 3px;
            }
            QCheckBox {
                color: #cdd6f4;
                spacing: 10px;
                font-size: 12px;
                min-height: 24px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #45475a;
                background-color: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #89b4fa;
                border-color: #89b4fa;
            }
            QCheckBox::indicator:hover {
                border-color: #89b4fa;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #cdd6f4; margin-bottom: 4px; background: transparent;")
        layout.addWidget(title)
        
        # ===== Temperature Group =====
        temp_group, temp_layout = self._create_group("Temperature")
        
        # Warning threshold
        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(40, 100)
        self._threshold_spin.setSuffix(" °C")
        temp_layout.addWidget(self._create_row("Warning Threshold:", self._threshold_spin))
        
        # Update interval
        self._interval_combo = QComboBox()
        self._interval_combo.addItems(["0.5 seconds", "1 second", "2 seconds"])
        temp_layout.addWidget(self._create_row("Update Interval:", self._interval_combo))
        
        layout.addWidget(temp_group)
        
        # ===== Appearance Group =====
        appearance_group, appearance_layout = self._create_group("Appearance")
        
        # Text size
        self._size_combo = QComboBox()
        self._size_combo.addItems(["Small", "Medium", "Large"])
        appearance_layout.addWidget(self._create_row("Text Size:", self._size_combo))
        
        # Transparency
        transparency_widget = QWidget()
        transparency_inner = QHBoxLayout(transparency_widget)
        transparency_inner.setContentsMargins(0, 0, 0, 0)
        transparency_inner.setSpacing(8)
        
        self._transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self._transparency_slider.setRange(30, 90)
        self._transparency_slider.setTickInterval(10)
        self._transparency_slider.setMinimumWidth(120)
        
        self._transparency_label = QLabel("60%")
        self._transparency_label.setMinimumWidth(40)
        self._transparency_label.setStyleSheet("color: #89b4fa; font-weight: bold; background: transparent;")
        self._transparency_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        transparency_inner.addWidget(self._transparency_slider, 1)
        transparency_inner.addWidget(self._transparency_label)
        
        appearance_layout.addWidget(self._create_row("Transparency:", transparency_widget))
        
        layout.addWidget(appearance_group)
        
        # ===== Behavior Group =====
        behavior_group, behavior_layout = self._create_group("Behavior")
        
        self._always_on_top_check = QCheckBox("Always on top")
        behavior_layout.addWidget(self._always_on_top_check)
        
        self._start_with_windows_check = QCheckBox("Start with Windows")
        behavior_layout.addWidget(self._start_with_windows_check)
        
        layout.addWidget(behavior_group)
        
        # Reset position button
        self._reset_btn = QPushButton("Reset Widget Position")
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e2e;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5c2e7;
            }
        """)
        layout.addWidget(self._reset_btn)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self._cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self._cancel_btn)
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        button_layout.addWidget(self._apply_btn)
        
        layout.addLayout(button_layout)
    
    def _load_values(self):
        """Load current values from configuration."""
        self._threshold_spin.setValue(self._config.warning_threshold)
        
        # Update interval
        interval = self._config.update_interval
        interval_idx = {0.5: 0, 1.0: 1, 2.0: 2}.get(interval, 1)
        self._interval_combo.setCurrentIndex(interval_idx)
        
        # Text size
        size = self._config.text_size
        size_idx = {'small': 0, 'medium': 1, 'large': 2}.get(size, 1)
        self._size_combo.setCurrentIndex(size_idx)
        
        # Transparency
        self._transparency_slider.setValue(self._config.transparency)
        self._transparency_label.setText(f"{self._config.transparency}%")
        
        # Checkboxes
        self._always_on_top_check.setChecked(self._config.always_on_top)
        self._start_with_windows_check.setChecked(self._config.start_with_windows)
    
    def _setup_connections(self):
        """Set up signal connections."""
        self._transparency_slider.valueChanged.connect(
            lambda v: self._transparency_label.setText(f"{v}%")
        )
        
        self._reset_btn.clicked.connect(self._on_reset_position)
        self._cancel_btn.clicked.connect(self.reject)
        self._apply_btn.clicked.connect(self._on_apply)
    
    def _on_reset_position(self):
        """Handle reset position button click."""
        self.position_reset.emit()
    
    def _on_apply(self):
        """Apply settings and close dialog."""
        # Save all settings
        self._config.warning_threshold = self._threshold_spin.value()
        
        # Update interval
        interval_map = {0: 0.5, 1: 1.0, 2: 2.0}
        self._config.update_interval = interval_map.get(
            self._interval_combo.currentIndex(), 1.0
        )
        
        # Text size
        size_map = {0: 'small', 1: 'medium', 2: 'large'}
        self._config.text_size = size_map.get(
            self._size_combo.currentIndex(), 'medium'
        )
        
        # Transparency
        self._config.transparency = self._transparency_slider.value()
        
        # Checkboxes
        self._config.always_on_top = self._always_on_top_check.isChecked()
        self._config.start_with_windows = self._start_with_windows_check.isChecked()
        
        # Emit signal and close
        self.settings_changed.emit()
        self.accept()
    
    def showEvent(self, event):
        """Refresh values when dialog is shown."""
        super().showEvent(event)
        self._load_values()
