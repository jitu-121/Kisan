"""
Top Bar Navigation & System Status Widget for Project KISAN.
Scoped QSS styling to eliminate wireframe box outlines on child widgets.
"""

from datetime import datetime
from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class TopBarWidget(QFrame):
    """
    Top Bar Widget matching reference mockup. Height: 42px.
    """
    location_toggle_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBarWidget")
        self.location_enabled = True
        self.system_online = True
        self._init_ui()
        self._start_timers()

    def _init_ui(self):
        self.setFixedHeight(42)
        self.setStyleSheet(f"""
            QFrame#TopBarWidget {{
                background-color: {COLOR_BACKGROUND};
                border-bottom: 1px solid #141c2e;
            }}
            QFrame#TopBarWidget QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(12)

        # 1. LEFT: Logo + Signal Icon + Date & Time Stack
        left_widget = QWidget(self)
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        logo_ic = QLabel(left_widget)
        pix = qta.icon("fa5s.seedling", color=COLOR_PRIMARY_ACCENT).pixmap(QSize(20, 20))
        logo_ic.setPixmap(pix)

        signal_ic = QLabel(left_widget)
        pix_sig = qta.icon("fa5s.signal", color="#38bdf8").pixmap(QSize(14, 14))
        signal_ic.setPixmap(pix_sig)

        dt_box = QVBoxLayout()
        dt_box.setSpacing(0)
        self.time_label = QLabel("10:30 AM", left_widget)
        self.time_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        self.date_label = QLabel("24 May 2025", left_widget)
        self.date_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 9px; border: none; background: transparent;")

        dt_box.addWidget(self.time_label)
        dt_box.addWidget(self.date_label)

        left_layout.addWidget(logo_ic)
        left_layout.addWidget(signal_ic)
        left_layout.addLayout(dt_box)

        # 2. CENTER: Main Title + Tagline
        center_widget = QWidget(self)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(1)
        center_layout.setAlignment(Qt.AlignCenter)

        title_lbl = QLabel("SMART SOIL ANALYSIS & CROP RECOMMENDATION", center_widget)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 13px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;"
        )

        tagline_lbl = QLabel("🌱 AI Powered • Offline • For Better Farming 🌱", center_widget)
        tagline_lbl.setAlignment(Qt.AlignCenter)
        tagline_lbl.setStyleSheet(
            f"color: {COLOR_PRIMARY_ACCENT}; font-family: {FONT_FAMILY}; font-size: 10px; font-weight: 600; border: none; background: transparent;"
        )

        center_layout.addWidget(title_lbl)
        center_layout.addWidget(tagline_lbl)

        # 3. RIGHT: Wifi Icon + SYSTEM ONLINE Pill Badge
        right_widget = QWidget(self)
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        wifi_ic = QLabel(right_widget)
        pix_wifi = qta.icon("fa5s.wifi", color=COLOR_PRIMARY_ACCENT).pixmap(QSize(15, 15))
        wifi_ic.setPixmap(pix_wifi)

        self.status_badge = QLabel("● SYSTEM ONLINE", right_widget)
        self.status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: #0b2e16;
                color: {COLOR_PRIMARY_ACCENT};
                border: 1px solid #166534;
                border-radius: 12px;
                padding: 3px 10px;
                font-family: {FONT_FAMILY};
                font-size: 10px;
                font-weight: 700;
            }}
        """)

        right_layout.addWidget(wifi_ic)
        right_layout.addWidget(self.status_badge)

        # Assemble TopBar
        layout.addWidget(left_widget)
        layout.addStretch(1)
        layout.addWidget(center_widget)
        layout.addStretch(1)
        layout.addWidget(right_widget)

    def _start_timers(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock_and_status)
        self.clock_timer.start(1000)

    def _update_clock_and_status(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%I:%M %p"))
        self.date_label.setText(now.strftime("%d %b %Y"))

        # Check sensor probe hardware status
        from services.sensor_service import SensorService
        sensor_data = SensorService.read_sensor_data()
        if sensor_data.get("is_online", False):
            self.status_badge.setText("● SENSOR ONLINE")
            self.status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: #0b2e16;
                    color: {COLOR_PRIMARY_ACCENT};
                    border: 1px solid #166534;
                    border-radius: 12px;
                    padding: 3px 10px;
                    font-family: {FONT_FAMILY};
                    font-size: 10px;
                    font-weight: 700;
                }}
            """)
        else:
            self.status_badge.setText("● SENSOR OFFLINE")
            self.status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: #2e0b0b;
                    color: #ef5350;
                    border: 1px solid #651616;
                    border-radius: 12px;
                    padding: 3px 10px;
                    font-family: {FONT_FAMILY};
                    font-size: 10px;
                    font-weight: 700;
                }}
            """)

