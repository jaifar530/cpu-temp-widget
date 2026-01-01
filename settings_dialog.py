"""
Settings dialog for CPU Temperature Widget.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSpinBox, QComboBox, QSlider, QCheckBox,
    QPushButton, QGroupBox, QFrame, QSpacerItem, QSizePolicy
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
        self.setFixedSize(400, 480)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 16px;
                padding: 16px;
                padding-top: 24px;
                color: #cdd6f4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                top: 4px;
                padding: 0 6px;
                background-color: #1e1e2e;
            }
            QSpinBox, QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 120px;
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
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #cdd6f4;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #313244;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #89b4fa;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
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
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
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
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
            QPushButton#primaryButton {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton#primaryButton:hover {
                background-color: #b4befe;
            }
            QPushButton#dangerButton {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton#dangerButton:hover {
                background-color: #f5c2e7;
            }
        """)
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #cdd6f4; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Temperature group
        temp_group = QGroupBox("Temperature")
        temp_layout = QGridLayout(temp_group)
        temp_layout.setSpacing(12)
        
        # Warning threshold
        temp_layout.addWidget(QLabel("Warning Threshold:"), 0, 0)
        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(40, 100)
        self._threshold_spin.setSuffix(" °C")
        temp_layout.addWidget(self._threshold_spin, 0, 1)
        
        # Update interval
        temp_layout.addWidget(QLabel("Update Interval:"), 1, 0)
        self._interval_combo = QComboBox()
        self._interval_combo.addItems(["0.5 seconds", "1 second", "2 seconds"])
        temp_layout.addWidget(self._interval_combo, 1, 1)
        
        layout.addWidget(temp_group)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)
        appearance_layout.setSpacing(12)
        
        # Text size
        appearance_layout.addWidget(QLabel("Text Size:"), 0, 0)
        self._size_combo = QComboBox()
        self._size_combo.addItems(["Small", "Medium", "Large"])
        appearance_layout.addWidget(self._size_combo, 0, 1)
        
        # Transparency
        appearance_layout.addWidget(QLabel("Transparency:"), 1, 0)
        
        transparency_layout = QHBoxLayout()
        self._transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self._transparency_slider.setRange(30, 90)
        self._transparency_slider.setTickInterval(10)
        
        self._transparency_label = QLabel("60%")
        self._transparency_label.setMinimumWidth(40)
        self._transparency_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        transparency_layout.addWidget(self._transparency_slider)
        transparency_layout.addWidget(self._transparency_label)
        appearance_layout.addLayout(transparency_layout, 1, 1)
        
        layout.addWidget(appearance_group)
        
        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        behavior_layout.setSpacing(12)
        
        self._always_on_top_check = QCheckBox("Always on top")
        behavior_layout.addWidget(self._always_on_top_check)
        
        self._start_with_windows_check = QCheckBox("Start with Windows")
        behavior_layout.addWidget(self._start_with_windows_check)
        
        layout.addWidget(behavior_group)
        
        # Reset position button
        self._reset_btn = QPushButton("Reset Widget Position")
        self._reset_btn.setObjectName("dangerButton")
        layout.addWidget(self._reset_btn)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self._cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self._cancel_btn)
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setObjectName("primaryButton")
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
