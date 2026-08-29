"""
About System Page View for Project KISAN.
Structured 4-Card Architecture wrapped in QScrollArea with ICAR-NIASM Baramati reference,
XAI (SHAP) metrics, embedded hardware specs, and dynamic version badge.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
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
)


class AboutPage(QWidget):
    """About System Information View with 4 Structured Cards and QScrollArea."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)

        # Header Row: System Identity & Top Version Badge
        hdr_layout = QHBoxLayout()
        hdr_title = QLabel("System Architecture & Specifications", self)
        hdr_title.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 800; font-family: {FONT_FAMILY};"
        )
        hdr_layout.addWidget(hdr_title)
        hdr_layout.addStretch(1)

        # Top Version Badge
        version_badge = QLabel("Project KISAN • v2.4 (Edge-AI Inference Engine)", self)
        version_badge.setStyleSheet("""
            background-color: #0b2914;
            color: #55ff55;
            font-size: 12px;
            font-weight: 700;
            border: 1px solid #28a745;
            border-radius: 6px;
            padding: 4px 10px;
        """)
        hdr_layout.addWidget(version_badge)
        main_layout.addLayout(hdr_layout)

        # Scroll Area Setup (Guarantees zero UI overflow on 7" displays)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #0d140d;
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #28a745;
                min-height: 25px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #55ff55;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
            }
        """)

        # Container Widget inside ScrollArea
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(10)

        # Fetch model metadata dynamically
        model_info = RecommendationService.get_model_info()

        # ==========================================
        # CARD 1: Core Purpose & Mission
        # ==========================================
        card1 = self._create_section_card(
            icon_name="fa5s.bullseye",
            title="1. Core Mission & Edge-AI Precision Agronomy",
            items=[
                ("Primary Mission:", "Empower smallholder & regional farmers with real-time, off-grid soil diagnostic intelligence."),
                ("Operating Architecture:", "100% Offline-First execution on embedded Linux hardware with zero cloud dependency."),
                ("Core Vision:", "Automate empirical soil telemetry conversion into optimized NPK dosing and crop recommendations.")
            ]
        )
        content_layout.addWidget(card1)

        # ==========================================
        # CARD 2: AI / ML & Explainable AI (XAI) Stack
        # ==========================================
        card2 = self._create_section_card(
            icon_name="fa5s.brain",
            title="2. AI / ML Stack & Explainable AI (XAI) Engine",
            items=[
                ("Crop Classifier Model:", f"Multi-Class Ensemble ({model_info['model_name']} - {model_info['model_version']})"),
                ("Trained Input Features:", "Soil Nitrogen (N), Phosphorus (P), Potassium (K), pH, Moisture, & Temperature"),
                ("Supported Crop Classes:", f"{model_info['classes_count']} Dynamic Maharashtra Agricultural Crops"),
                ("Explainable AI (XAI):", "SHAP (SHapley Additive exPlanations) for local feature contribution transparency"),
                ("Decision Constraints:", "Real-time 72-hour rainfall cluster probability & soil leaching risk integration")
            ]
        )
        content_layout.addWidget(card2)

        # ==========================================
        # CARD 3: Scientific Calibration & ICAR-NIASM Baramati Standards
        # ==========================================
        card3 = self._create_section_card(
            icon_name="fa5s.flask",
            title="3. Scientific Calibration & ICAR-NIASM Baramati Standards",
            items=[
                ("Reference Research Partner:", "ICAR - National Institute of Abiotic Stress Management (NIASM), Baramati"),
                ("Nitrogen (N) Lab Method:", "Alkaline Permanganate Method (Subbiah & Asija Standard)"),
                ("Phosphorus (P) Lab Method:", "Olsen / Bray Colorimetric Method (Spectrophotometry)"),
                ("Potassium (K) Lab Method:", "Neutral Ammonium Acetate Extraction (Flame Photometry)"),
                ("Empirical Calibration Model:", "Multi-variate Polynomial Regression Model (R² > 0.91, MAE Reduction > 75%)")
            ]
        )
        content_layout.addWidget(card3)

        # ==========================================
        # CARD 4: Hardware Specs & Edge Telemetry
        # ==========================================
        card4 = self._create_section_card(
            icon_name="fa5s.microchip",
            title="4. Embedded Hardware & Edge Telemetry Specifications",
            items=[
                ("Compute Host Hardware:", "Raspberry Pi 5 (Quad-Core ARM Cortex-A76 @ 2.4GHz, 4GB/8GB LPDDR4X SDRAM)"),
                ("Soil Telemetry Probe:", "Industrial ZTS-3002 (7-in-1 Soil Telemetry via RS485 / Modbus RTU Protocol)"),
                ("Display Panel Unit:", "Waveshare 7-inch 1024x600 IPS Capacitive Multi-Touchscreen"),
                ("Storage & Persistence:", "Local SQLite Edge Database + Open-Meteo Satellite JSON Cache File")
            ]
        )
        content_layout.addWidget(card4)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

    def _create_section_card(self, icon_name: str, title: str, items: list) -> QFrame:
        """Helper to construct a structured section card frame."""
        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background-color: #0d150d;
                border: 1px solid #1a2c1a;
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(8)

        # Card Title Header
        title_layout = QHBoxLayout()
        icon_lbl = QLabel(card)
        icon_lbl.setPixmap(qta.icon(icon_name, color=COLOR_PRIMARY_ACCENT).pixmap(20, 20))
        
        title_lbl = QLabel(title, card)
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 700; font-family: {FONT_FAMILY};")
        
        title_layout.addWidget(icon_lbl)
        title_layout.addWidget(title_lbl)
        title_layout.addStretch(1)
        card_layout.addLayout(title_layout)

        # Items Grid Layout
        grid = QGridLayout()
        grid.setContentsMargins(4, 2, 4, 2)
        grid.setSpacing(6)

        for row, (label, value) in enumerate(items):
            lbl_widget = QLabel(label, card)
            lbl_widget.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 600;")
            
            val_widget = QLabel(value, card)
            val_widget.setWordWrap(True)
            val_widget.setStyleSheet(f"color: #e0f0e0; font-size: 12px; font-weight: 700;")

            grid.addWidget(lbl_widget, row, 0, Qt.AlignTop)
            grid.addWidget(val_widget, row, 1, Qt.AlignTop)

        grid.setColumnStretch(1, 1)
        card_layout.addLayout(grid)

        return card
