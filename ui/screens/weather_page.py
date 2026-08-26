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
        self.setMinimumHeight(280)
        self.setMaximumHeight(360)
        
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
        layout.setSpacing(8)


        # Get Real/Cached Weather Data
        w = WeatherService.get_weather("Baramati", location_permission_enabled=True)
        is_offline = w.get("is_offline", False)
        from_cache = w.get("from_cache", False)

        # Header Row with Location and Online/Offline Badge
        hdr_layout = QHBoxLayout()
        hdr = QLabel(f"Live Weather Forecast — {w['location']}", self)
        hdr.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 700; font-family: {FONT_FAMILY};")
        hdr_layout.addWidget(hdr)

        status_lbl = QLabel(self)
        if is_offline:
            status_lbl.setText(" Offline (Showing Cache)")
            status_lbl.setStyleSheet("color: #ffaa00; font-size: 13px; font-weight: 700; background-color: #332200; border: 1px solid #ffaa00; border-radius: 4px; padding: 3px 8px;")
        elif from_cache:
            status_lbl.setText(f" Cached (Expires: {w['updated_at']})")
            status_lbl.setStyleSheet("color: #77dd77; font-size: 13px; font-weight: 700; background-color: #113311; border: 1px solid #77dd77; border-radius: 4px; padding: 3px 8px;")
        else:
            status_lbl.setText(" Live Updated")
            status_lbl.setStyleSheet("color: #55ff55; font-size: 13px; font-weight: 700; background-color: #003300; border: 1px solid #55ff55; border-radius: 4px; padding: 3px 8px;")
        
        hdr_layout.addWidget(status_lbl)
        hdr_layout.addStretch(1)
        
        # Sub-header detailing last updated timestamp
        time_info = QLabel(f"Last updated: {w['updated_at']}", self)
        time_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        hdr_layout.addWidget(time_info)
        
        layout.addLayout(hdr_layout)

        # Main Row containing Current Weather Card & Cloud Cover Card side-by-side (saves space on 7")
        main_cards_row = QHBoxLayout()
        main_cards_row.setSpacing(12)

        # Current Weather Card (Left)
        main_card = QFrame(self)
        main_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        main_card.setMinimumHeight(130)
        mc_layout = QHBoxLayout(main_card)
        mc_layout.setContentsMargins(18, 14, 18, 14)

        w_ic = QLabel(main_card)
        w_ic.setPixmap(qta.icon(w["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(56, 56))

        w_info = QVBoxLayout()
        w_temp = QLabel(f"{w['temperature']} • {w['condition']}", main_card)
        w_temp.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 800; font-family: {FONT_FAMILY};")

        w_sub = QLabel(
            f"Humidity: {w['humidity']} • Wind: {w['wind']}\nRain Probability: {w['rain_chance']}",
            main_card
        )
        w_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; line-height: 18px;")

        w_info.addWidget(w_temp)
        w_info.addWidget(w_sub)

        mc_layout.addWidget(w_ic)
        mc_layout.addLayout(w_info, 1)
        main_cards_row.addWidget(main_card, 3)

        # Option A: Visual Cloud Coverage Card (Right)
        cloud_card = QFrame(self)
        cloud_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        cloud_card.setMinimumHeight(130)
        cc_layout = QVBoxLayout(cloud_card)
        cc_layout.setContentsMargins(18, 12, 18, 12)
        cc_layout.setSpacing(6)

        cc_title_layout = QHBoxLayout()
        cc_ic = QLabel(cloud_card)
        cc_ic.setPixmap(qta.icon("fa5s.cloud", color=COLOR_PRIMARY_ACCENT).pixmap(20, 20))
        cc_title = QLabel("Sky Cloud Cover", cloud_card)
        cc_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; font-family: {FONT_FAMILY};")
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
                height: 20px;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #2e7d32;
                border-radius: 3px;
            }
        """)
        cc_layout.addWidget(cc_bar)

        # Dynamic agriculture advice based on cloud cover
        if cloud_val < 25:
            adv_text = "Clear Sky: Excellent for solar energy generation & field work."
        elif cloud_val < 65:
            adv_text = "Partial Clouds: Normal sunlight. Suitable for outdoor crop tasks."
        else:
            adv_text = "Heavy Clouds: Reduced light. Monitor for sudden showers."
        
        cc_adv = QLabel(adv_text, cloud_card)
        cc_adv.setWordWrap(True)
        cc_adv.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; font-style: italic;")
        cc_layout.addWidget(cc_adv)

        main_cards_row.addWidget(cloud_card, 2)
        layout.addLayout(main_cards_row)

        # 5-Day Forecast Strip Header
        f_hdr = QLabel("5-Day Weather Forecast:", self)
        f_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 700; font-family: {FONT_FAMILY};")
        layout.addWidget(f_hdr)

        # 5-Day Forecast Cards Row
        f_row = QHBoxLayout()
        f_row.setSpacing(10)

        for day in w["forecast"]:
            f_box = QFrame(self)
            f_box.setStyleSheet("background-color: #0d140d; border: 1px solid #182418; border-radius: 6px;")
            f_box.setMinimumHeight(95)
            fb_layout = QVBoxLayout(f_box)
            fb_layout.setContentsMargins(6, 6, 6, 6)
            fb_layout.setAlignment(Qt.AlignCenter)
            fb_layout.setSpacing(2)

            d_lbl = QLabel(f"{day['day']} ({day['date']})", f_box)
            d_lbl.setAlignment(Qt.AlignCenter)
            d_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 700; font-family: {FONT_FAMILY};")

            d_ic = QLabel(f_box)
            d_ic.setAlignment(Qt.AlignCenter)
            d_ic.setPixmap(qta.icon(day["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(24, 24))

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

        # Cloud Radar Section Header
        r_hdr = QLabel("Live Cloud Coverage Radar Map:", self)
        r_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 700; font-family: {FONT_FAMILY};")
        layout.addWidget(r_hdr)

        # Cloud Radar Map Widget
        self.radar_widget = CloudRadarWidget(cloud_val, self)
        layout.addWidget(self.radar_widget)


