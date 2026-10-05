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
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from utils.i18n import get_language_manager
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class TopBarWidget(QFrame):
    """
    Top Bar Widget matching reference mockup with Top Right Language Selector. Height: 42px.
    """
    location_toggle_changed = pyqtSignal(bool)
    sidebar_toggle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBarWidget")
        self.location_enabled = True
        self.system_online = True
        self.i18n = get_language_manager()
        self._init_ui()
        self._start_timers()

        # Connect to language change signal
        self.i18n.language_changed.connect(self._on_language_changed)

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

        # 1. LEFT: Hamburger Toggle + Logo + Signal Icon + Date & Time Stack
        left_widget = QWidget(self)
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.toggle_btn = QPushButton(left_widget)
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setToolTip("Toggle Sidebar Navigation")
        self.toggle_btn.setIcon(qta.icon("fa5s.bars", color=COLOR_PRIMARY_ACCENT))
        self.toggle_btn.setIconSize(QSize(16, 16))
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d1424;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #131b2e;
                border: 1px solid #22c55e;
            }
            QPushButton:pressed {
                background-color: #14532d;
            }
        """)
        self.toggle_btn.clicked.connect(self.sidebar_toggle_requested.emit)

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

        left_layout.addWidget(self.toggle_btn)
        left_layout.addWidget(logo_ic)
        left_layout.addWidget(signal_ic)
        left_layout.addLayout(dt_box)

        # 2. CENTER: Main Title + Tagline
        center_widget = QWidget(self)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(1)
        center_layout.setAlignment(Qt.AlignCenter)

        self.title_lbl = QLabel('<span style="color: #ffffff; font-weight: 800;">KRUSHI </span><span style="color: #22c55e; font-weight: 800;">AI</span>', center_widget)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet(
            f"font-family: {FONT_FAMILY}; font-size: 16px; letter-spacing: 2px; border: none; background: transparent;"
        )

        self.tagline_lbl = QLabel(f"🌱 {self.i18n.tr('app_tagline')} 🌱", center_widget)
        self.tagline_lbl.setAlignment(Qt.AlignCenter)
        self.tagline_lbl.setStyleSheet(
            f"color: {COLOR_PRIMARY_ACCENT}; font-family: {FONT_FAMILY}; font-size: 10px; font-weight: 600; border: none; background: transparent;"
        )

        center_layout.addWidget(self.title_lbl)
        center_layout.addWidget(self.tagline_lbl)

        # 3. RIGHT: Wifi Icon + System Status Badge + TOP-RIGHT LANGUAGE SELECTOR
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

        # TOP RIGHT CORNER LANGUAGE SELECTOR BUTTON
        self.btn_lang = QPushButton(right_widget)
        self.btn_lang.setFixedHeight(28)
        self.btn_lang.setCursor(Qt.PointingHandCursor)
        self.btn_lang.setToolTip("Select Language / भाषा चुनें")
        self.btn_lang.setStyleSheet(f"""
            QPushButton {{
                background-color: #0d1424;
                color: {COLOR_PRIMARY_ACCENT};
                border: 1px solid #166534;
                border-radius: 14px;
                padding: 3px 10px;
                font-family: {FONT_FAMILY};
                font-size: 11px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: #131b2e;
                border: 1px solid #22c55e;
            }}
        """)
        self._update_lang_btn_text()

        self.lang_menu = QMenu(self.btn_lang)
        self.lang_menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #ffffff;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
                font-family: Inter, Roboto, sans-serif;
                font-size: 12px;
                font-weight: 700;
            }
            QMenu::item:selected {
                background-color: #2E7D32;
                color: #ffffff;
            }
        """)

        act_en = self.lang_menu.addAction("🇬🇧 English")
        act_hi = self.lang_menu.addAction("🇮🇳 हिंदी (Hindi)")
        act_mr = self.lang_menu.addAction("🇮🇳 मराठी (Marathi)")

        act_en.triggered.connect(lambda: self.i18n.set_language("en"))
        act_hi.triggered.connect(lambda: self.i18n.set_language("hi"))
        act_mr.triggered.connect(lambda: self.i18n.set_language("mr"))

        self.btn_lang.setMenu(self.lang_menu)

        right_layout.addWidget(wifi_ic)
        right_layout.addWidget(self.status_badge)
        right_layout.addWidget(self.btn_lang)

        # Assemble TopBar
        layout.addWidget(left_widget)
        layout.addStretch(1)
        layout.addWidget(center_widget)
        layout.addStretch(1)
        layout.addWidget(right_widget)

    def _update_lang_btn_text(self):
        curr = self.i18n.get_language()
        lang_display_map = {
            "en": "🌐 EN",
            "hi": "🌐 हि (HI)",
            "mr": "🌐 म (MR)"
        }
        display_text = lang_display_map.get(curr, "🌐 EN")
        self.btn_lang.setText(display_text)

    def _on_language_changed(self, lang_code: str):
        self._update_lang_btn_text()
        self.tagline_lbl.setText(f"🌱 {self.i18n.tr('app_tagline')} 🌱")

    def _start_timers(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock_and_status)
        self.clock_timer.start(1000)

    def _update_clock_and_status(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%I:%M %p"))
        self.date_label.setText(now.strftime("%d %b %Y"))

        from services.sensor_service import SensorService
        sensor_data = SensorService.read_sensor_data()
        if sensor_data.get("is_online", False):
            self.status_badge.setText(f"● {self.i18n.tr('sensor_online')}")
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
            self.status_badge.setText(f"● {self.i18n.tr('sensor_offline')}")
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


