"""
Settings Page View for Project KISAN.
System configuration, Wifi toggle, location override, and sensor calibration settings.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
    FONT_SIZE_TITLE,
)


class SettingsPage(QWidget):
    """Application Settings View."""
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        title = QLabel("System Settings & Configuration", self)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_TITLE}; font-weight: 700;")
        layout.addWidget(title)

        # Settings Card
        card = QFrame(self)
        card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(14, 12, 14, 12)
        card_l.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(10)

        # 1. Wifi Toggle
        grid.addWidget(QLabel("Wi-Fi Interface:", card), 0, 0)
        self.wifi_btn = QPushButton("Wi-Fi: ENABLED", card)
        self.wifi_btn.setFixedHeight(30)
        self.wifi_btn.setCursor(Qt.PointingHandCursor)
        self.wifi_btn.setStyleSheet(f"background-color: #192c19; color: {COLOR_PRIMARY_ACCENT}; border: 1px solid {COLOR_PRIMARY_ACCENT}; border-radius: 4px; font-weight: 700; font-size: 11px;")
        grid.addWidget(self.wifi_btn, 0, 1)

        # 2. Location Permission
        grid.addWidget(QLabel("Location GPS Auto-Detection:", card), 1, 0)
        self.loc_btn = QPushButton("GPS Detection: ALLOWED", card)
        self.loc_btn.setFixedHeight(30)
        self.loc_btn.setCursor(Qt.PointingHandCursor)
        self.loc_btn.setStyleSheet(f"background-color: #192c19; color: {COLOR_PRIMARY_ACCENT}; border: 1px solid {COLOR_PRIMARY_ACCENT}; border-radius: 4px; font-weight: 700; font-size: 11px;")
        grid.addWidget(self.loc_btn, 1, 1)

        # 3. Manual Location Override
        grid.addWidget(QLabel("Manual Location Override:", card), 2, 0)
        self.loc_input = QLineEdit("Pune, Maharashtra", card)
        self.loc_input.setFixedHeight(30)
        self.loc_input.setStyleSheet("background: #0a0f0a; color: #e5e5e5; border: 1px solid #1a2a1a; border-radius: 4px; padding: 0 8px; font-size: 11px;")
        grid.addWidget(self.loc_input, 2, 1)

        # 4. Sensor Probe Calibration
        grid.addWidget(QLabel("Soil Sensor Calibration:", card), 3, 0)
        btn_calib = QPushButton("Run Sensor Probe Calibration Routine", card)
        btn_calib.setFixedHeight(30)
        btn_calib.setCursor(Qt.PointingHandCursor)
        btn_calib.setStyleSheet("background: #182818; color: #00d97e; border: 1px solid #00d97e; border-radius: 4px; font-weight: 600; font-size: 11px;")
        grid.addWidget(btn_calib, 3, 1)

        card_l.addLayout(grid)
        layout.addWidget(card)
        layout.addStretch(1)
