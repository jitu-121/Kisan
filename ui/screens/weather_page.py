"""
Weather Report Page View for Project KISAN.
Full detailed weather report with 5-day forecast, cached/offline indicator, and custom cloud card.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap, QColor, QRadialGradient
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)
import qtawesome as qta
import random
import os
from services.weather_service import WeatherService
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
)


class CloudRadarWidget(QWidget):
    """Dynamic cloud radar map displaying live RainViewer satellite data (Option B)."""

    def __init__(self, cloud_cover: int = 0, parent=None):
        super().__init__(parent)
        self.cloud_cover = cloud_cover
        self.setMinimumHeight(380)
        self.setMaximumHeight(650)
        
        # Load composite live radar map (Option B) if available, fallback to base map
        composite_path = "database/weather_radar_composite.jpg"
        if os.path.exists(composite_path):
            self.radar_map = QPixmap(composite_path)
        else:
            self.radar_map = QPixmap("assets/weather_map_base.jpg")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.radar_map.isNull():
            # Fallback if image not found
            painter.fillRect(self.rect(), QColor("#101910"))
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignCenter, "Map Asset Loading...")
            return

        # Scale and center the radar map
        scaled_map = self.radar_map.scaled(
            self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        x_offset = (self.width() - scaled_map.width()) // 2
        y_offset = (self.height() - scaled_map.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_map)

        # Draw a clean outline border
        painter.setPen(QColor("#1a291a"))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class WeatherPage(QWidget):
    """Expanded Weather View with Cache status and Cloud Density indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)


        # Get Real/Cached Weather Data
        w = WeatherService.get_weather("Baramati", location_permission_enabled=True)
        is_offline = w.get("is_offline", False)
        from_cache = w.get("from_cache", False)
        synced_ago = w.get("synced_ago", "2h ago")
        agronomy = w.get("agronomy", {})
        ai_advisory = w.get("ai_advisory", "")

        # Header Row with Location and Online/Offline Badge
        hdr_layout = QHBoxLayout()
        hdr = QLabel(f"Live Weather Forecast — {w['location']}", self)
        hdr.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 700; font-family: {FONT_FAMILY};")
        hdr_layout.addWidget(hdr)

        status_lbl = QLabel(self)
        if is_offline:
            status_lbl.setText(f" ⚡ Edge Cache Active • {synced_ago}")
            status_lbl.setStyleSheet("color: #ffaa00; font-size: 12px; font-weight: 700; background-color: #332200; border: 1px solid #ffaa00; border-radius: 4px; padding: 2px 6px;")
        elif from_cache:
            status_lbl.setText(f" ⚡ Edge Cache Active • {synced_ago}")
            status_lbl.setStyleSheet("color: #77dd77; font-size: 12px; font-weight: 700; background-color: #113311; border: 1px solid #77dd77; border-radius: 4px; padding: 2px 6px;")
        else:
            status_lbl.setText(" 🟢 Live Updated")
            status_lbl.setStyleSheet("color: #55ff55; font-size: 12px; font-weight: 700; background-color: #003300; border: 1px solid #55ff55; border-radius: 4px; padding: 2px 6px;")
        
        hdr_layout.addWidget(status_lbl)
        hdr_layout.addStretch(1)
        
        # Sub-header detailing last updated timestamp
        time_info = QLabel(f"Last updated: {w['updated_at']}", self)
        time_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        hdr_layout.addWidget(time_info)
        
        layout.addLayout(hdr_layout)

        # Main Row containing Current Weather Card & Cloud Cover Card side-by-side
        main_cards_row = QHBoxLayout()
        main_cards_row.setSpacing(10)

        # Current Weather Card with Agronomy Metrics (Left) - Compact Vertical Height
        main_card = QFrame(self)
        main_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        main_card.setMinimumHeight(115)
        main_card.setMaximumHeight(125)
        mc_main_layout = QVBoxLayout(main_card)
        mc_main_layout.setContentsMargins(12, 6, 12, 6)
        mc_main_layout.setSpacing(4)

        mc_layout = QHBoxLayout()
        w_ic = QLabel(main_card)
        w_ic.setPixmap(qta.icon(w["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(40, 40))

        w_info = QVBoxLayout()
        w_temp = QLabel(f"{w['temperature']} • {w['condition']}", main_card)
        w_temp.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 800; font-family: {FONT_FAMILY};")

        w_sub = QLabel(
            f"Humidity: {w['humidity']} • Wind: {w['wind']} • Rain Prob: {w['rain_chance']}",
            main_card
        )
        w_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        w_info.addWidget(w_temp)
        w_info.addWidget(w_sub)

        mc_layout.addWidget(w_ic)
        mc_layout.addLayout(w_info, 1)
        mc_main_layout.addLayout(mc_layout)

        # Agronomy Metrics Micro-Strip (ET0, Soil Leaching Risk, Spray Window)
        agronomy_strip = QHBoxLayout()
        agronomy_strip.setSpacing(6)

        et0_val = agronomy.get("et0", "-- mm/day")
        leaching = agronomy.get("leaching_risk", "--")
        spray_status = agronomy.get("spray_status", "--")

        et_chip = QLabel(f"💧 ET₀: {et0_val}", main_card)
        et_chip.setStyleSheet("background-color: #182818; color: #aaffaa; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; border: 1px solid #284428;")

        leach_color = "#ff6666" if "CRITICAL" in leaching or "HIGH" in leaching else "#ffcc00" if "MODERATE" in leaching else "#77dd77"
        leach_bg = "#331111" if "CRITICAL" in leaching or "HIGH" in leaching else "#332a00" if "MODERATE" in leaching else "#113311"
        leach_chip = QLabel(f"🧪 Leaching: {leaching}", main_card)
        leach_chip.setStyleSheet(f"background-color: {leach_bg}; color: {leach_color}; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; border: 1px solid {leach_color};")

        spray_color = "#77dd77" if spray_status == "OPTIMAL" else "#ffcc00" if spray_status == "MODERATE" else "#ff6666"
        spray_chip = QLabel(f"🌬️ Spray Window: {spray_status}", main_card)
        spray_chip.setStyleSheet(f"background-color: #0f2028; color: {spray_color}; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; border: 1px solid #1a3848;")

        agronomy_strip.addWidget(et_chip)
        agronomy_strip.addWidget(leach_chip)
        agronomy_strip.addWidget(spray_chip)
        agronomy_strip.addStretch(1)

        mc_main_layout.addLayout(agronomy_strip)
        main_cards_row.addWidget(main_card, 3)

        # Option A: Visual Cloud Coverage Card (Right) - Compact Vertical Height
        cloud_card = QFrame(self)
        cloud_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        cloud_card.setMinimumHeight(115)
        cloud_card.setMaximumHeight(125)
        cc_layout = QVBoxLayout(cloud_card)
        cc_layout.setContentsMargins(12, 6, 12, 6)
        cc_layout.setSpacing(4)

        cc_title_layout = QHBoxLayout()
        cc_ic = QLabel(cloud_card)
        cc_ic.setPixmap(qta.icon("fa5s.cloud", color=COLOR_PRIMARY_ACCENT).pixmap(16, 16))
        cc_title = QLabel("Sky Cloud Cover", cloud_card)
        cc_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700; font-family: {FONT_FAMILY};")
        cc_title_layout.addWidget(cc_ic)
        cc_title_layout.addWidget(cc_title)
        cc_title_layout.addStretch(1)
        cc_layout.addLayout(cc_title_layout)

        cloud_val = w.get("cloud_cover", 0)
        cc_bar = QProgressBar(cloud_card)
        cc_bar.setRange(0, 100)
        cc_bar.setValue(cloud_val)
        cc_bar.setTextVisible(True)
        cc_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #1a291a;
                border-radius: 4px;
                background-color: #050a05;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 16px;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #2e7d32;
                border-radius: 3px;
            }
        """)
        cc_layout.addWidget(cc_bar)

        # Dynamic agriculture advice based on cloud cover
        if cloud_val < 25:
            adv_text = "Clear Sky: Excellent for solar generation & field operations."
        elif cloud_val < 65:
            adv_text = "Partial Clouds: Normal sunlight. Suitable for crop work."
        else:
            adv_text = "Heavy Clouds: Reduced light. Monitor for precipitation."
        
        cc_adv = QLabel(adv_text, cloud_card)
        cc_adv.setWordWrap(True)
        cc_adv.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-style: italic;")
        cc_layout.addWidget(cc_adv)

        main_cards_row.addWidget(cloud_card, 2)
        layout.addLayout(main_cards_row)

        # 5-Day Forecast Strip Header
        f_hdr = QLabel("5-Day Weather Forecast:", self)
        f_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 700; font-family: {FONT_FAMILY};")
        layout.addWidget(f_hdr)

        # 5-Day Forecast Cards Row - Compact Height
        f_row = QHBoxLayout()
        f_row.setSpacing(6)

        for day in w["forecast"]:
            f_box = QFrame(self)
            f_box.setStyleSheet("background-color: #0d140d; border: 1px solid #182418; border-radius: 6px;")
            f_box.setMinimumHeight(80)
            fb_layout = QVBoxLayout(f_box)
            fb_layout.setContentsMargins(3, 3, 3, 3)
            fb_layout.setAlignment(Qt.AlignCenter)
            fb_layout.setSpacing(1)

            d_lbl = QLabel(f"{day['day']} ({day['date']})", f_box)
            d_lbl.setAlignment(Qt.AlignCenter)
            d_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: 700; font-family: {FONT_FAMILY};")

            d_ic = QLabel(f_box)
            d_ic.setAlignment(Qt.AlignCenter)
            d_ic.setPixmap(qta.icon(day["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(20, 20))

            t_lbl = QLabel(day["temp"], f_box)
            t_lbl.setAlignment(Qt.AlignCenter)
            t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-family: {FONT_FAMILY};")

            r_lbl = QLabel(f"Rain: {day['rain_chance']}", f_box)
            r_lbl.setAlignment(Qt.AlignCenter)
            r_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-family: {FONT_FAMILY};")

            fb_layout.addWidget(d_lbl)
            fb_layout.addWidget(d_ic)
            fb_layout.addWidget(t_lbl)
            fb_layout.addWidget(r_lbl)

            f_row.addWidget(f_box)

        layout.addLayout(f_row)

        # Smart AI Field Advisory Collapsible Button (The AI Link)
        if ai_advisory:
            is_warn = "Heavy rainfall" in ai_advisory or "Unfavorable" in ai_advisory or "High heat" in ai_advisory
            btn_bg = "#221700" if is_warn else "#0a1e0d"
            btn_border = "#d99000" if is_warn else "#28a745"
            btn_color = "#ffcc00" if is_warn else "#55ff55"
            card_bg = "#140f02" if is_warn else "#061408"

            from PyQt5.QtWidgets import QPushButton

            adv_btn = QPushButton(self)
            adv_btn.setText(" ⚠️  AI Field Action Advisory  •  Click to View Insights  ▼")
            adv_btn.setCursor(Qt.PointingHandCursor)
            adv_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_bg};
                    border: 1px solid {btn_border};
                    color: {btn_color};
                    font-size: 12px;
                    font-weight: 700;
                    font-family: {FONT_FAMILY};
                    border-radius: 6px;
                    padding: 6px 12px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: #382600;
                    color: #ffffff;
                    border-color: #ffaa00;
                }}
            """)

            adv_card = QFrame(self)
            adv_card.setStyleSheet(f"background-color: {card_bg}; border: 1px solid {btn_border}; border-radius: 8px;")
            adv_card.setVisible(False)  # Hidden by default until clicked!

            ac_layout = QHBoxLayout(adv_card)
            ac_layout.setContentsMargins(14, 10, 14, 10)
            ac_layout.setSpacing(0)

            # Pure advisory text without icon or inner rectangle border
            adv_txt = QLabel(ai_advisory, adv_card)
            adv_txt.setWordWrap(True)
            adv_txt.setStyleSheet(f"color: #f0f0f0; font-size: 12px; font-weight: 500; font-family: {FONT_FAMILY}; line-height: 18px; border: none; background: transparent;")

            ac_layout.addWidget(adv_txt, 1)

            def _toggle_advisory():
                currently_visible = adv_card.isVisible()
                adv_card.setVisible(not currently_visible)
                if not currently_visible:
                    adv_btn.setText(" ⚠️  AI Field Action Advisory  •  Hide Insights  ▲")
                else:
                    adv_btn.setText(" ⚠️  AI Field Action Advisory  •  Click to View Insights  ▼")

            adv_btn.clicked.connect(_toggle_advisory)

            layout.addWidget(adv_btn)
            layout.addWidget(adv_card)

        # Cloud Radar Section Header
        r_hdr = QLabel("Live Cloud Coverage Radar Map:", self)
        r_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 700; font-family: {FONT_FAMILY};")
        layout.addWidget(r_hdr)

        # Cloud Radar Map Widget (Expanded height with stretch)
        self.radar_widget = CloudRadarWidget(cloud_val, self)
        layout.addWidget(self.radar_widget, 1)



