"""
Weather Report Page View for Project KISAN.
Full detailed weather report with 5-day forecast.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from services.weather_service import WeatherService
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
)


class WeatherPage(QWidget):
    """Expanded Weather Report View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        w = WeatherService.get_weather("Pune", location_permission_enabled=True)

        # Header
        hdr = QLabel(f"Live Weather Forecast — {w['location']}", self)
        hdr.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_TITLE}; font-weight: 700;")
        layout.addWidget(hdr)

        # Current Weather Main Card
        main_card = QFrame(self)
        main_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        mc_layout = QHBoxLayout(main_card)
        mc_layout.setContentsMargins(16, 12, 16, 12)

        w_ic = QLabel(main_card)
        w_ic.setPixmap(qta.icon(w["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(48, 48))

        w_info = QVBoxLayout()
        w_temp = QLabel(f"{w['temperature']} • {w['condition']}", main_card)
        w_temp.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 800;")

        w_sub = QLabel(f"Humidity: {w['humidity']} • Wind Speed: {w['wind']} • Rain Probability: {w['rain_chance']} • UV Index: {w['uv_index']}", main_card)
        w_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        w_info.addWidget(w_temp)
        w_info.addWidget(w_sub)

        mc_layout.addWidget(w_ic)
        mc_layout.addLayout(w_info, 1)

        layout.addWidget(main_card)

        # 5-Day Forecast Strip Header
        f_hdr = QLabel("5-Day Weather Forecast:", self)
        f_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 700;")
        layout.addWidget(f_hdr)

        # 5-Day Forecast Cards Row
        f_row = QHBoxLayout()
        f_row.setSpacing(8)

        for day in w["forecast"]:
            f_box = QFrame(self)
            f_box.setStyleSheet("background-color: #0d140d; border: 1px solid #182418; border-radius: 6px;")
            fb_layout = QVBoxLayout(f_box)
            fb_layout.setContentsMargins(8, 8, 8, 8)
            fb_layout.setAlignment(Qt.AlignCenter)

            d_lbl = QLabel(f"{day['day']} ({day['date']})", f_box)
            d_lbl.setAlignment(Qt.AlignCenter)
            d_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 700;")

            d_ic = QLabel(f_box)
            d_ic.setAlignment(Qt.AlignCenter)
            d_ic.setPixmap(qta.icon(day["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(24, 24))

            t_lbl = QLabel(day["temp"], f_box)
            t_lbl.setAlignment(Qt.AlignCenter)
            t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px;")

            r_lbl = QLabel(f"Rain: {day['rain_chance']}", f_box)
            r_lbl.setAlignment(Qt.AlignCenter)
            r_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")

            fb_layout.addWidget(d_lbl)
            fb_layout.addWidget(d_ic)
            fb_layout.addWidget(t_lbl)
            fb_layout.addWidget(r_lbl)

            f_row.addWidget(f_box)

        layout.addLayout(f_row)
        layout.addStretch(1)
