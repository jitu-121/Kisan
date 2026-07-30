"""
About System Page View for Project KISAN.
Displays project identity, ML model info, system status, KVK Baramati credits, and contact info.
"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from services.recommendation_service import RecommendationService
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
)


class AboutPage(QWidget):
    """About System Information View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        # Header Card: Identity & Tagline
        hdr_card = QFrame(self)
        hdr_card.setStyleSheet("background-color: #101910; border: 1px solid #00d97e; border-radius: 8px;")
        hc_layout = QHBoxLayout(hdr_card)
        hc_layout.setContentsMargins(14, 10, 14, 10)

        logo = QLabel(hdr_card)
        logo.setPixmap(qta.icon("fa5s.seedling", color=COLOR_PRIMARY_ACCENT).pixmap(36, 36))

        info = QVBoxLayout()
        t = QLabel("PROJECT KISAN", hdr_card)
        t.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 800; letter-spacing: 1px;")

        tag = QLabel("AI Powered • Offline • For Better Farming", hdr_card)
        tag.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 700;")

        info.addWidget(t)
        info.addWidget(tag)

        hc_layout.addWidget(logo)
        hc_layout.addLayout(info, 1)

        layout.addWidget(hdr_card)

        # Details Grid: Model Info & Hardware Status
        model_info = RecommendationService.get_model_info()

        grid_card = QFrame(self)
        grid_card.setStyleSheet("background-color: #0d140d; border: 1px solid #1a291a; border-radius: 6px;")
        gc_l = QGridLayout(grid_card)
        gc_l.setContentsMargins(12, 10, 12, 10)
        gc_l.setSpacing(8)

        details = [
            ("Application Version:", "Project KISAN v1.0.0 (Release Build)"),
            ("ML Recommendation Model:", f"{model_info['model_name']} ({model_info['model_version']})"),
            ("Supported Crop Classes:", f"{model_info['classes_count']} Crops Dynamic Multi-Output"),
            ("Target Display Hardware:", "Waveshare 7-inch 1024x600 IPS Capacitive Touchscreen"),
            ("Host Compute Device:", "Raspberry Pi (Linux Off-Grid Embedded Engine)"),
            ("Soil Sensor Status:", "● Modbus Probe Active (RS485 Protocol)"),
            ("Data Source & Credits:", "KVK Baramati Soil Testing Laboratory & Agricultural Research"),
            ("Developer & Project Info:", "Antigravity Smart AgTech Engineering Team"),
        ]

        for idx, (label, val) in enumerate(details):
            l_w = QLabel(label, grid_card)
            l_w.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 600;")
            v_w = QLabel(val, grid_card)
            v_w.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 700;")

            gc_l.addWidget(l_w, idx, 0)
            gc_l.addWidget(v_w, idx, 1)

        layout.addWidget(grid_card)
        layout.addStretch(1)
