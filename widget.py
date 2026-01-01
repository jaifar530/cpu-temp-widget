"""
Floating widget window for CPU Temperature Widget.
A translucent, frameless, always-on-top overlay that displays CPU temperature.
"""

from PyQt6.QtCore import (
    Qt, QPoint, QPropertyAnimation, QEasingCurve, 
    QTimer, pyqtProperty, QSize, QRect
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QBrush, QPen, 
    QFont, QFontDatabase, QScreen, QCursor
)
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QMenu, QApplication, QGraphicsDropShadowEffect
)

from config import get_config


class TemperatureWidget(QWidget):
    """
    Floating translucent widget that displays CPU temperature.
    
    Features:
    - Frameless, transparent background
    - Always-on-top (configurable)
    - Click-and-drag repositioning
    - Lock position mode with click-through
    - Animated color transitions for warning state
    - HOT indicator for sustained high temperature
    """
    
    # Colors
    COLOR_NORMAL = QColor(220, 220, 230)       # Light gray-white
    COLOR_WARNING = QColor(255, 90, 90)        # Red
    COLOR_BACKGROUND = QColor(20, 20, 30, 160) # Semi-transparent dark
    COLOR_HOT_GLOW = QColor(255, 60, 60, 180)  # Red glow
    
    def __init__(self):
        super().__init__()
        self._config = get_config()
        self._temperature = 0.0
        self._is_warning = False
        self._show_hot = False
        self._is_error = False
        self._drag_position = QPoint()
        self._current_color = self.COLOR_NORMAL
        
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        self._setup_context_menu()
        self._apply_config()
        self._restore_position()
    
    def _setup_window(self):
        """Configure window flags and attributes."""
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |  # Doesn't show in taskbar
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowFlags(flags)
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        
        # Set minimum size
        self.setMinimumSize(120, 50)
        self.setMaximumSize(300, 100)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        
        # Temperature label
        self._temp_label = QLabel("CPU: --°C")
        self._temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # HOT indicator (hidden by default)
        self._hot_label = QLabel("HOT")
        self._hot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hot_label.setStyleSheet("""
            QLabel {
                color: #ff5a5a;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 2px;
            }
        """)
        self._hot_label.hide()
        
        # Warning icon (for errors)
        self._warning_icon = QLabel("⚠")
        self._warning_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._warning_icon.setStyleSheet("color: #ffaa00; font-size: 12px;")
        self._warning_icon.hide()
        self._warning_icon.setToolTip("Unable to read CPU temperature.\nRun as administrator for accurate readings.")
        
        # Layout
        temp_row = QHBoxLayout()
        temp_row.addWidget(self._warning_icon)
        temp_row.addWidget(self._temp_label)
        temp_row.addStretch()
        
        layout.addWidget(self._hot_label)
        layout.addLayout(temp_row)
        
        self._update_font()
    
    def _setup_animations(self):
        """Set up color animation for warning transitions."""
        # Color animation
        self._color_animation = QPropertyAnimation(self, b"textColor")
        self._color_animation.setDuration(300)
        self._color_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # HOT indicator pulse animation
        self._hot_timer = QTimer(self)
        self._hot_timer.setInterval(500)
        self._hot_timer.timeout.connect(self._pulse_hot_indicator)
        self._hot_visible = True
    
    def _setup_context_menu(self):
        """Set up the right-click context menu."""
        self._context_menu = QMenu(self)
        
        # Lock position action
        self._lock_action = self._context_menu.addAction("Lock Position")
        self._lock_action.setCheckable(True)
        self._lock_action.setChecked(self._config.position_locked)
        self._lock_action.triggered.connect(self._toggle_lock)
        
        self._context_menu.addSeparator()
        
        # Settings action
        self._settings_action = self._context_menu.addAction("Settings...")
        
        self._context_menu.addSeparator()
        
        # Exit action
        self._exit_action = self._context_menu.addAction("Exit")
        self._exit_action.triggered.connect(QApplication.quit)
        
        # Apply dark style to menu
        self._context_menu.setStyleSheet("""
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
        """)
    
    def _apply_config(self):
        """Apply current configuration settings."""
        # Always on top
        self._update_always_on_top()
        
        # Click-through mode
        self._update_click_through()
        
        # Font size
        self._update_font()
    
    def _update_font(self):
        """Update the font based on configuration."""
        font = QFont("Segoe UI", self._config.font_size)
        font.setWeight(QFont.Weight.Medium)
        self._temp_label.setFont(font)
        self._update_label_style()
        
        # Adjust size hint
        self.adjustSize()
    
    def _update_label_style(self):
        """Update label style with current color."""
        color = self._current_color
        self._temp_label.setStyleSheet(f"""
            QLabel {{
                color: rgb({color.red()}, {color.green()}, {color.blue()});
                background: transparent;
            }}
        """)
    
    def _update_always_on_top(self):
        """Update the always-on-top state."""
        flags = self.windowFlags()
        
        if self._config.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        
        # Re-show the widget (required after changing flags)
        if self.isVisible():
            self.show()
    
    def _update_click_through(self):
        """Update click-through mode based on lock state."""
        flags = self.windowFlags()
        
        if self._config.position_locked:
            flags |= Qt.WindowType.WindowTransparentForInput
        else:
            flags &= ~Qt.WindowType.WindowTransparentForInput
        
        self.setWindowFlags(flags)
        
        # Re-show the widget
        if self.isVisible():
            self.show()
    
    def _restore_position(self):
        """Restore the widget position from config."""
        x, y = self._config.position
        
        if x is not None and y is not None:
            # Validate position is within screen bounds
            screen = QApplication.primaryScreen()
            if screen:
                screen_geo = screen.availableGeometry()
                x = max(screen_geo.left(), min(x, screen_geo.right() - self.width()))
                y = max(screen_geo.top(), min(y, screen_geo.bottom() - self.height()))
            
            self.move(x, y)
        else:
            # Center on primary screen
            self._center_on_screen()
    
    def _center_on_screen(self):
        """Center the widget on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = screen_geo.center().x() - self.width() // 2
            y = screen_geo.top() + 50  # Near top of screen
            self.move(x, y)
    
    def _toggle_lock(self, checked: bool):
        """Toggle position lock state."""
        self._config.position_locked = checked
        self._update_click_through()
    
    def _pulse_hot_indicator(self):
        """Pulse the HOT indicator visibility."""
        self._hot_visible = not self._hot_visible
        self._hot_label.setVisible(self._hot_visible and self._show_hot)
    
    # Qt property for color animation
    def _get_text_color(self) -> QColor:
        return self._current_color
    
    def _set_text_color(self, color: QColor):
        self._current_color = color
        self._update_label_style()
    
    textColor = pyqtProperty(QColor, _get_text_color, _set_text_color)
    
    # Public methods
    def update_temperature(self, temperature: float):
        """Update the displayed temperature."""
        self._is_error = temperature < 0
        
        if self._is_error:
            self._temp_label.setText("CPU: --°C")
            self._warning_icon.show()
        else:
            self._temperature = temperature
            self._temp_label.setText(f"CPU: {temperature:.0f}°C")
            self._warning_icon.hide()
    
    def set_warning_state(self, is_warning: bool, show_hot: bool):
        """
        Set the warning state for temperature display.
        
        Args:
            is_warning: Whether temperature is above threshold
            show_hot: Whether to show the HOT indicator
        """
        # Update HOT indicator
        self._show_hot = show_hot
        
        if show_hot:
            self._hot_label.show()
            if not self._hot_timer.isActive():
                self._hot_timer.start()
        else:
            self._hot_label.hide()
            self._hot_timer.stop()
        
        # Animate color change
        if is_warning != self._is_warning:
            self._is_warning = is_warning
            
            target_color = self.COLOR_WARNING if is_warning else self.COLOR_NORMAL
            
            self._color_animation.stop()
            self._color_animation.setStartValue(self._current_color)
            self._color_animation.setEndValue(target_color)
            self._color_animation.start()
    
    def apply_settings(self):
        """Apply updated settings from configuration."""
        self._apply_config()
        self._lock_action.setChecked(self._config.position_locked)
    
    def reset_position(self):
        """Reset widget position to center of screen."""
        self._config.reset_position()
        self._center_on_screen()
    
    def connect_settings_action(self, callback):
        """Connect the settings action to a callback."""
        self._settings_action.triggered.connect(callback)
    
    # Event handlers
    def paintEvent(self, event):
        """Custom paint event for translucent background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate background opacity from config
        opacity = self._config.transparency / 100.0
        bg_color = QColor(
            self.COLOR_BACKGROUND.red(),
            self.COLOR_BACKGROUND.green(),
            self.COLOR_BACKGROUND.blue(),
            int(255 * opacity)
        )
        
        # Draw rounded rectangle background
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 10, 10)
        
        # Fill background
        painter.fillPath(path, QBrush(bg_color))
        
        # Draw subtle border
        border_color = QColor(80, 80, 100, int(100 * opacity))
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        
        # Draw hot glow if in warning state
        if self._show_hot:
            glow_color = QColor(
                self.COLOR_HOT_GLOW.red(),
                self.COLOR_HOT_GLOW.green(),
                self.COLOR_HOT_GLOW.blue(),
                int(60 * opacity)
            )
            painter.setPen(QPen(glow_color, 2))
            painter.drawPath(path)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._config.position_locked:
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._context_menu.exec(event.globalPosition().toPoint())
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            if not self._config.position_locked and not self._drag_position.isNull():
                new_pos = event.globalPosition().toPoint() - self._drag_position
                
                # Constrain to screen bounds
                screen = QApplication.screenAt(new_pos)
                if screen is None:
                    screen = QApplication.primaryScreen()
                
                if screen:
                    screen_geo = screen.availableGeometry()
                    new_pos.setX(max(screen_geo.left(), min(new_pos.x(), screen_geo.right() - self.width())))
                    new_pos.setY(max(screen_geo.top(), min(new_pos.y(), screen_geo.bottom() - self.height())))
                
                self.move(new_pos)
                event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = QPoint()
            # Save position
            if not self._config.position_locked:
                pos = self.pos()
                self._config.position = (pos.x(), pos.y())
            event.accept()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Restore position when shown
        self._restore_position()
    
    def closeEvent(self, event):
        """Handle close event."""
        # Save position before closing
        if not self._config.position_locked:
            pos = self.pos()
            self._config.position = (pos.x(), pos.y())
        super().closeEvent(event)
