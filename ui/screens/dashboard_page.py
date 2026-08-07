"""
Dashboard Page View for Project KISAN.
Scoped QSS styling to eliminate all wireframe box outlines on child widgets.
Matches reference UI design mockup pixel-for-pixel with clean dark navy aesthetics.
"""

from PyQt5.QtCore import QSize, Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from services.recommendation_service import RecommendationService
from services.sensor_service import SensorService
from services.weather_service import WeatherService
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_BTN_BLUE,
    COLOR_BTN_GOLD,
    COLOR_BTN_RED,
    COLOR_BTN_TEAL,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class DashboardPage(QWidget):
    """Dashboard View with clean scoped QSS styling."""
    navigate_to_page = pyqtSignal(int)
    export_report_trigger = pyqtSignal()
    shutdown_trigger = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_widgets = {}
        self._init_ui()

        # Telemetry timer for real-time sensor updates (checks every 2 seconds)
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self._run_realtime_scan)
        self.telemetry_timer.start(2000)

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        # 1. TOP ROW: 5 Sensor Cards Strip
        sensor_strip = self._build_sensor_strip()
        layout.addWidget(sensor_strip)

        # 2. MIDDLE ROW: Crop Rec Card (Left) & Weather Card (Right)
        middle_widget = QWidget(self)
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(8)

        crop_card = self._build_crop_recommendation_card()
        weather_card = self._build_weather_card()

        middle_layout.addWidget(crop_card, 5)
        middle_layout.addWidget(weather_card, 5)

        layout.addWidget(middle_widget, 1)

        # 3. LOWER ROW: Report Last Analysis Summary Strip
        report_strip = self._build_last_report_strip()
        layout.addWidget(report_strip)

        # 4. BOTTOM ROW: 4 Action Buttons
        action_bar = self._build_action_bar()
        layout.addWidget(action_bar)

    def _build_sensor_strip(self) -> QWidget:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        data = SensorService.read_sensor_data()

        sensors = [
            ("ph", "pH", data["display_values"]["ph"], data["tags"]["ph"], "fa5s.flask", "#38bdf8"),
            ("nitrogen", "Nitrogen (N)", data["display_values"]["nitrogen"], data["tags"]["nitrogen"], "fa5s.seedling", "#22c55e"),
            ("phosphorus", "Phosphorus (P)", data["display_values"]["phosphorus"], data["tags"]["phosphorus"], "fa5s.tint", "#f59e0b"),
            ("potassium", "Potassium (K)", data["display_values"]["potassium"], data["tags"]["potassium"], "fa5s.leaf", "#10b981"),
            ("moisture", "Moisture", data["display_values"]["moisture"], data["tags"]["moisture"], "fa5s.tint", "#06b6d4"),
        ]

        self.sensor_widgets = {}

        for key, title, val, tag, icon, icon_color in sensors:
            card = QFrame(container)
            card.setObjectName("SensorCard")
            card.setFixedHeight(54)
            card.setStyleSheet("""
                QFrame#SensorCard {
                    background-color: #0d1424;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame#SensorCard QLabel {
                    border: none;
                    background: transparent;
                }
            """)

            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(8, 4, 8, 4)
            c_layout.setSpacing(8)

            ic = QLabel(card)
            ic.setPixmap(qta.icon(icon, color=icon_color).pixmap(QSize(20, 20)))

            v_box = QVBoxLayout()
            v_box.setSpacing(0)

            t_lbl = QLabel(title, card)
            t_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-weight: 500; border: none; background: transparent;")

            v_lbl = QLabel(val, card)
            v_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 800; border: none; background: transparent;")

            sub_lbl = QLabel(tag, card)
            sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; border: none; background: transparent;")

            v_box.addWidget(t_lbl)
            v_box.addWidget(v_lbl)
            v_box.addWidget(sub_lbl)

            c_layout.addWidget(ic)
            c_layout.addLayout(v_box, 1)

            layout.addWidget(card)

            # Store references to update them dynamically
            self.sensor_widgets[key] = (v_lbl, sub_lbl)

        return container

    def _run_realtime_scan(self):
        if not self.isVisible():
            return

        data = SensorService.read_sensor_data()

        # Update the sensor strip widgets in real time
        sensors = ["ph", "nitrogen", "phosphorus", "potassium", "moisture"]
        for key in sensors:
            if key in self.sensor_widgets:
                v_lbl, sub_lbl = self.sensor_widgets[key]
                v_lbl.setText(data["display_values"].get(key, "--"))
                
                # If online, show status tag, otherwise show offline message
                tag_str = data["tags"].get(key, "")
                sub_lbl.setText(tag_str)

    def _build_crop_recommendation_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("CropCard")
        card.setStyleSheet("""
            QFrame#CropCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #071c0f, stop:1 #0d2816);
                border: 1px solid #164e26;
                border-radius: 10px;
            }
            QFrame#CropCard QLabel {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Title
        title_box = QHBoxLayout()
        ic = QLabel(card)
        ic.setPixmap(qta.icon("fa5s.seedling", color=COLOR_PRIMARY_ACCENT).pixmap(16, 16))

        t_lbl = QLabel("CROP RECOMMENDATION", card)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")

        title_box.addWidget(ic)
        title_box.addWidget(t_lbl)
        title_box.addStretch(1)

        layout.addLayout(title_box)

        # Best Match Center Section
        best_box = QHBoxLayout()
        best_box.setSpacing(12)

        # Circle Crop Icon
        crop_circle = QFrame(card)
        crop_circle.setObjectName("CropCircle")
        crop_circle.setFixedSize(52, 52)
        crop_circle.setStyleSheet("""
            QFrame#CropCircle {
                background-color: #14381e;
                border: 2px solid #22c55e;
                border-radius: 26px;
            }
            QFrame#CropCircle QLabel {
                border: none;
                background: transparent;
            }
        """)
        cc_layout = QVBoxLayout(crop_circle)
        cc_layout.setContentsMargins(0, 0, 0, 0)
        cc_layout.setAlignment(Qt.AlignCenter)

        c_ic = QLabel(crop_circle)
        c_ic.setPixmap(qta.icon("fa5s.leaf", color=COLOR_PRIMARY_ACCENT).pixmap(24, 24))
        cc_layout.addWidget(c_ic)

        # Best Match Name & Score
        bm_info = QVBoxLayout()
        bm_info.setSpacing(2)

        bm_lbl = QLabel("Best Match", card)
        bm_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 500; border: none; background: transparent;")

        crop_name = QLabel("SUGARCANE", card)
        crop_name.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 18px; font-weight: 900; letter-spacing: 1px; border: none; background: transparent;")

        score_pill = QLabel("Confidence Score   92.4 %", card)
        score_pill.setStyleSheet("""
            QLabel {
                background-color: #0e3019;
                color: #22c55e;
                border: 1px solid #166534;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
            }
        """)

        bm_info.addWidget(bm_lbl)
        bm_info.addWidget(crop_name)
        bm_info.addWidget(score_pill)

        best_box.addWidget(crop_circle)
        best_box.addLayout(bm_info, 1)

        layout.addLayout(best_box)

        # Other Suitable Crops Section
        other_lbl = QLabel("Other Suitable Crops", card)
        other_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        layout.addWidget(other_lbl)

        others_row = QHBoxLayout()
        others_row.setSpacing(6)

        runner_ups = [
            ("POMEGRANATE", "83.1%", "fa5s.apple-alt"),
            ("JOWAR", "74.6%", "fa5s.seedling"),
            ("COTTON", "68.3%", "fa5s.cloud"),
        ]

        for c_title, c_score, c_icon in runner_ups:
            r_card = QFrame(card)
            r_card.setObjectName("RunnerCard")
            r_card.setStyleSheet("""
                QFrame#RunnerCard {
                    background-color: #081a0e;
                    border: 1px solid #14381e;
                    border-radius: 6px;
                }
                QFrame#RunnerCard QLabel {
                    border: none;
                    background: transparent;
                }
            """)
            rc_l = QVBoxLayout(r_card)
            rc_l.setContentsMargins(4, 4, 4, 4)
            rc_l.setAlignment(Qt.AlignCenter)
            rc_l.setSpacing(2)

            r_ic = QLabel(r_card)
            r_ic.setAlignment(Qt.AlignCenter)
            r_ic.setPixmap(qta.icon(c_icon, color=COLOR_PRIMARY_ACCENT).pixmap(16, 16))

            r_name = QLabel(c_title, r_card)
            r_name.setAlignment(Qt.AlignCenter)
            r_name.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 9px; font-weight: 700; border: none; background: transparent;")

            r_val = QLabel(c_score, r_card)
            r_val.setAlignment(Qt.AlignCenter)
            r_val.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 9px; font-weight: 600; border: none; background: transparent;")

            rc_l.addWidget(r_ic)
            rc_l.addWidget(r_name)
            rc_l.addWidget(r_val)

            others_row.addWidget(r_card)

        layout.addLayout(others_row)

        # Bottom Action Button
        btn_view = QPushButton("🌱 View Detailed Recommendation", card)
        btn_view.setFixedHeight(28)
        btn_view.setCursor(Qt.PointingHandCursor)
        btn_view.setStyleSheet(f"""
            QPushButton {{
                background-color: #0b2e16;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid #166534;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 10px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #14532d;
            }}
        """)
        btn_view.clicked.connect(lambda: self.navigate_to_page.emit(2))

        layout.addWidget(btn_view)
        return card

    def _build_weather_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("WeatherCard")
        card.setStyleSheet("""
            QFrame#WeatherCard {
                background-color: #0d1424;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QFrame#WeatherCard QLabel {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header
        hdr_box = QHBoxLayout()
        ic = QLabel(card)
        ic.setPixmap(qta.icon("fa5s.cloud", color="#38bdf8").pixmap(16, 16))

        t_lbl = QLabel("WEATHER REPORT", card)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")

        loc_lbl = QLabel("Baramati, Maharashtra 📍", card)
        loc_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; border: none; background: transparent;")

        hdr_box.addWidget(ic)
        hdr_box.addWidget(t_lbl)
        hdr_box.addStretch(1)
        hdr_box.addWidget(loc_lbl)

        layout.addLayout(hdr_box)

        # Main Weather Stats Row
        mw_box = QHBoxLayout()
        mw_box.setSpacing(10)

        # Temp & Sun/Cloud Icon
        sun_ic = QLabel(card)
        sun_ic.setPixmap(qta.icon("fa5s.cloud-sun", color="#f59e0b").pixmap(42, 42))

        temp_box = QVBoxLayout()
        temp_box.setSpacing(0)
        temp_lbl = QLabel("32°C", card)
        temp_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 900; border: none; background: transparent;")

        cond_lbl = QLabel("Partly Cloudy", card)
        cond_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; border: none; background: transparent;")

        temp_box.addWidget(temp_lbl)
        temp_box.addWidget(cond_lbl)

        mw_box.addWidget(sun_ic)
        mw_box.addLayout(temp_box)
        mw_box.addStretch(1)

        # Weather Details Side Panel
        details_grid = QGridLayout()
        details_grid.setSpacing(4)

        items = [
            ("💧 Humidity", "56 %"),
            ("💨 Wind Speed", "14 km/h"),
            ("🌧️ Rain Chance", "20 %"),
            ("☀️ UV Index", "6 (High)"),
        ]

        for r, (label, val) in enumerate(items):
            l_w = QLabel(label, card)
            l_w.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; border: none; background: transparent;")
            v_w = QLabel(f"▶  {val}", card)
            v_w.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 9px; font-weight: 700; border: none; background: transparent;")

            details_grid.addWidget(l_w, r, 0)
            details_grid.addWidget(v_w, r, 1)

        mw_box.addLayout(details_grid)
        layout.addLayout(mw_box)

        # 5 Day Forecast Strip
        f_hdr = QLabel("5 Day Forecast", card)
        f_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        layout.addWidget(f_hdr)

        f_row = QHBoxLayout()
        f_row.setSpacing(4)

        forecast_data = [
            ("SAT", "33° / 22°", "fa5s.sun", "#f59e0b"),
            ("SUN", "32° / 21°", "fa5s.cloud", "#94a3b8"),
            ("MON", "31° / 20°", "fa5s.cloud-showers-heavy", "#38bdf8"),
            ("TUE", "33° / 21°", "fa5s.cloud-sun", "#f59e0b"),
            ("WED", "34° / 22°", "fa5s.sun", "#f59e0b"),
        ]

        for day, temps, icon_n, icon_c in forecast_data:
            f_box = QFrame(card)
            f_box.setObjectName("ForecastCard")
            f_box.setStyleSheet("""
                QFrame#ForecastCard {
                    background-color: #090e1a;
                    border: 1px solid #162036;
                    border-radius: 6px;
                }
                QFrame#ForecastCard QLabel {
                    border: none;
                    background: transparent;
                }
            """)
            fb_l = QVBoxLayout(f_box)
            fb_l.setContentsMargins(4, 4, 4, 4)
            fb_l.setAlignment(Qt.AlignCenter)

            d_lbl = QLabel(day, f_box)
            d_lbl.setAlignment(Qt.AlignCenter)
            d_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-weight: 700; border: none; background: transparent;")

            i_lbl = QLabel(f_box)
            i_lbl.setAlignment(Qt.AlignCenter)
            i_lbl.setPixmap(qta.icon(icon_n, color=icon_c).pixmap(14, 14))

            t_lbl = QLabel(temps, f_box)
            t_lbl.setAlignment(Qt.AlignCenter)
            t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 8px; font-weight: 600; border: none; background: transparent;")

            fb_l.addWidget(d_lbl)
            fb_l.addWidget(i_lbl)
            fb_l.addWidget(t_lbl)

            f_row.addWidget(f_box)

        layout.addLayout(f_row)
        return card

    def _build_last_report_strip(self) -> QWidget:
        strip = QFrame(self)
        strip.setObjectName("ReportStrip")
        strip.setFixedHeight(48)
        strip.setStyleSheet("""
            QFrame#ReportStrip {
                background-color: #111428;
                border: 1px solid #1e2442;
                border-radius: 8px;
            }
            QFrame#ReportStrip QLabel {
                border: none;
                background: transparent;
            }
        """)

        layout = QHBoxLayout(strip)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(12)

        # Icon & Title
        title_box = QHBoxLayout()
        ic = QLabel(strip)
        ic.setPixmap(qta.icon("fa5s.clipboard-list", color="#a855f7").pixmap(16, 16))

        t_lbl = QLabel("REPORT – LAST ANALYSIS SUMMARY", strip)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; border: none; background: transparent;")

        title_box.addWidget(ic)
        title_box.addWidget(t_lbl)
        layout.addLayout(title_box)

        # Report Fields
        fields = [
            ("Date & Time", "24 May 2025\n10:28 AM", "fa5s.calendar-alt"),
            ("Sample ID", "KVK-BMT-250524", "fa5s.vial"),
            ("Soil Type", "Medium Black", "fa5s.mountain"),
            ("Recommendation", "Sugarcane", "fa5s.seedling"),
            ("Status", "Completed", "fa5s.check-circle"),
        ]

        for fname, fval, ficon in fields:
            box = QWidget(strip)
            b_l = QHBoxLayout(box)
            b_l.setContentsMargins(0, 0, 0, 0)
            b_l.setSpacing(4)

            b_ic = QLabel(box)
            b_ic.setPixmap(qta.icon(ficon, color=COLOR_PRIMARY_ACCENT if fname == "Status" else "#94a3b8").pixmap(12, 12))

            v_b = QVBoxLayout()
            v_b.setSpacing(0)

            fl = QLabel(fname, box)
            fl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8px; border: none; background: transparent;")
            fv = QLabel(fval, box)
            fv.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT if fname in ['Recommendation', 'Status'] else COLOR_TEXT_PRIMARY}; font-size: 9px; font-weight: 700; border: none; background: transparent;")

            v_b.addWidget(fl)
            v_b.addWidget(fv)

            b_l.addWidget(b_ic)
            b_l.addLayout(v_b)

            layout.addWidget(box)

        # Right Button
        btn_view = QPushButton("📄 View Full Report", strip)
        btn_view.setFixedHeight(28)
        btn_view.setCursor(Qt.PointingHandCursor)
        btn_view.setStyleSheet("""
            QPushButton {
                background-color: #3b2d6b;
                color: #ffffff;
                border: 1px solid #5b42a5;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #4c3a85;
            }
        """)
        btn_view.clicked.connect(lambda: self.navigate_to_page.emit(5))

        layout.addStretch(1)
        layout.addWidget(btn_view)

        return strip

    def _build_action_bar(self) -> QWidget:
        bar = QWidget(self)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        actions = [
            ("RE-ANALYZE SOIL", "fa5s.sync", COLOR_BTN_BLUE, lambda: self.navigate_to_page.emit(1)),
            ("EXPORT REPORT", "fa5s.download", COLOR_BTN_TEAL, self.export_report_trigger.emit),
            ("CALIBRATE SENSOR", "fa5s.crosshairs", COLOR_BTN_GOLD, lambda: self.navigate_to_page.emit(7)),
            ("SHUTDOWN SYSTEM", "fa5s.power-off", COLOR_BTN_RED, self.shutdown_trigger.emit),
        ]

        for text, icon, bg_color, slot in actions:
            btn = QPushButton(f"  {text}", bar)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(qta.icon(icon, color="#ffffff"))
            btn.setIconSize(QSize(14, 14))

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-family: {FONT_FAMILY};
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            btn.clicked.connect(slot)
            layout.addWidget(btn, 1)

        return bar
