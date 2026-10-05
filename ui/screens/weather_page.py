"""
Weather Report Page View for Project KISAN.
Full detailed weather report with 5-day forecast, cached/offline indicator, cloud cover card,
and AI Field Action Advisory — fully localized in English, Hindi, and Marathi.
"""

import os
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from services.weather_service import WeatherService
from utils.i18n import get_language_manager
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class CloudRadarWidget(QWidget):
    """Dynamic cloud radar map displaying live RainViewer satellite data."""

    def __init__(self, cloud_cover: int = 0, parent=None):
        super().__init__(parent)
        self.cloud_cover = cloud_cover
        self.setMinimumHeight(340)
        self.setMaximumHeight(500)

        composite_path = "database/weather_radar_composite.jpg"
        if os.path.exists(composite_path):
            self.radar_map = QPixmap(composite_path)
        else:
            self.radar_map = QPixmap("assets/weather_map_base.jpg")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.radar_map.isNull():
            painter.fillRect(self.rect(), QColor("#101910"))
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignCenter, "Map Asset Loading...")
            return

        scaled_map = self.radar_map.scaled(
            self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        x_offset = (self.width() - scaled_map.width()) // 2
        y_offset = (self.height() - scaled_map.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_map)

        painter.setPen(QColor("#1a291a"))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class WeatherPage(QWidget):
    """Expanded Weather View with full multi-language i18n support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_language_manager()
        self.weather_data = {}
        self._init_ui()
        self.i18n.language_changed.connect(self._on_language_changed)

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 8, 12, 8)
        self.main_layout.setSpacing(6)

        self._render_view()

    def _render_view(self):
        # Clear previous layout widgets if re-rendering
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear sub-layout items recursively
                self._clear_layout(item.layout())

        w = WeatherService.get_weather("Baramati", location_permission_enabled=True)
        self.weather_data = w

        is_offline = w.get("is_offline", False)
        from_cache = w.get("from_cache", False)
        synced_ago = w.get("synced_ago", "2h ago")
        agronomy = w.get("agronomy", {})
        ai_advisory = w.get("ai_advisory", {})

        # Header Row
        hdr_layout = QHBoxLayout()
        hdr_text = f"{self.i18n.tr('live_weather_forecast')} — {w['location']}"
        hdr = QLabel(hdr_text, self)
        hdr.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 19px; font-weight: 700; font-family: {FONT_FAMILY};")
        hdr_layout.addWidget(hdr)

        status_lbl = QLabel(self)
        if is_offline or from_cache:
            status_lbl.setText(f" ⚡ {self.i18n.tr('edge_cache_active')} • {synced_ago}")
            status_lbl.setStyleSheet("color: #77dd77; font-size: 11px; font-weight: 700; background-color: #113311; border: 1px solid #77dd77; border-radius: 4px; padding: 2px 6px;")
        else:
            status_lbl.setText(f" 🟢 {self.i18n.tr('live_updated')}")
            status_lbl.setStyleSheet("color: #55ff55; font-size: 11px; font-weight: 700; background-color: #003300; border: 1px solid #55ff55; border-radius: 4px; padding: 2px 6px;")

        hdr_layout.addWidget(status_lbl)
        hdr_layout.addStretch(1)

        time_info = QLabel(f"{self.i18n.tr('last_updated')}: {w['updated_at']}", self)
        time_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        hdr_layout.addWidget(time_info)

        self.main_layout.addLayout(hdr_layout)

        # Main Row: Current Weather Card (Left) + Cloud Cover Card (Right)
        main_cards_row = QHBoxLayout()
        main_cards_row.setSpacing(10)

        # Left Card: Current Weather
        main_card = QFrame(self)
        main_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        main_card.setFixedHeight(120)
        mc_main_layout = QVBoxLayout(main_card)
        mc_main_layout.setContentsMargins(12, 6, 12, 6)
        mc_main_layout.setSpacing(4)

        mc_layout = QHBoxLayout()
        w_ic = QLabel(main_card)
        w_ic.setPixmap(qta.icon(w["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(38, 38))

        w_info = QVBoxLayout()
        cond_trans = self._translate_condition(w["condition"])
        w_temp = QLabel(f"{w['temperature']} • {cond_trans}", main_card)
        w_temp.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 19px; font-weight: 800; font-family: {FONT_FAMILY};")

        w_sub_text = f"{self.i18n.tr('humidity')}: {w['humidity']} • {self.i18n.tr('wind')}: {w['wind']} • {self.i18n.tr('rain_prob')}: {w['rain_chance']}"
        w_sub = QLabel(w_sub_text, main_card)
        w_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        w_info.addWidget(w_temp)
        w_info.addWidget(w_sub)

        mc_layout.addWidget(w_ic)
        mc_layout.addLayout(w_info, 1)
        mc_main_layout.addLayout(mc_layout)

        # Agronomy Micro-Strip
        agronomy_strip = QHBoxLayout()
        agronomy_strip.setSpacing(6)

        et0_val = agronomy.get("et0", "-- mm/day")
        leaching = agronomy.get("leaching_risk", "--")
        spray_status = agronomy.get("spray_status", "--")

        et_chip = QLabel(f"💧 {self.i18n.tr('et0_label')}: {et0_val}", main_card)
        et_chip.setStyleSheet("background-color: #182818; color: #aaffaa; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; border: 1px solid #284428;")

        leach_trans = self._translate_leaching(leaching)
        leach_color = "#ff6666" if "CRITICAL" in leaching or "HIGH" in leaching else "#ffcc00" if "MODERATE" in leaching else "#77dd77"
        leach_bg = "#331111" if "CRITICAL" in leaching or "HIGH" in leaching else "#332a00" if "MODERATE" in leaching else "#113311"
        leach_chip = QLabel(f"🧪 {self.i18n.tr('leaching_label')}: {leach_trans}", main_card)
        leach_chip.setStyleSheet(f"background-color: {leach_bg}; color: {leach_color}; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; border: 1px solid {leach_color};")

        spray_trans = self._translate_spray(spray_status)
        spray_color = "#77dd77" if spray_status == "OPTIMAL" else "#ffcc00" if spray_status == "MODERATE" else "#ff6666"
        spray_chip = QLabel(f"🌬️ {self.i18n.tr('spray_window_label')}: {spray_trans}", main_card)
        spray_chip.setStyleSheet(f"background-color: #0f2028; color: {spray_color}; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; border: 1px solid #1a3848;")

        agronomy_strip.addWidget(et_chip)
        agronomy_strip.addWidget(leach_chip)
        agronomy_strip.addWidget(spray_chip)
        agronomy_strip.addStretch(1)

        mc_main_layout.addLayout(agronomy_strip)
        main_cards_row.addWidget(main_card, 3)

        # Right Card: Sky Cloud Cover
        cloud_card = QFrame(self)
        cloud_card.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 8px;")
        cloud_card.setFixedHeight(120)
        cc_layout = QVBoxLayout(cloud_card)
        cc_layout.setContentsMargins(12, 6, 12, 6)
        cc_layout.setSpacing(4)

        cc_title_layout = QHBoxLayout()
        cc_ic = QLabel(cloud_card)
        cc_ic.setPixmap(qta.icon("fa5s.cloud", color=COLOR_PRIMARY_ACCENT).pixmap(16, 16))
        cc_title = QLabel(self.i18n.tr("sky_cloud_cover"), cloud_card)
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

        if cloud_val < 25:
            adv_text = self.i18n.tr("cloud_advice_clear")
        elif cloud_val < 65:
            adv_text = self.i18n.tr("cloud_advice_partial")
        else:
            adv_text = self.i18n.tr("cloud_advice_heavy")

        cc_adv = QLabel(adv_text, cloud_card)
        cc_adv.setWordWrap(True)
        cc_adv.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-style: italic;")
        cc_layout.addWidget(cc_adv)

        main_cards_row.addWidget(cloud_card, 2)
        self.main_layout.addLayout(main_cards_row)

        # 5-Day Forecast Header
        f_hdr = QLabel(self.i18n.tr("5_day_weather_forecast"), self)
        f_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 700; font-family: {FONT_FAMILY};")
        self.main_layout.addWidget(f_hdr)

        # 5-Day Forecast Cards Row
        f_row = QHBoxLayout()
        f_row.setSpacing(6)

        for day in w["forecast"]:
            f_box = QFrame(self)
            f_box.setStyleSheet("background-color: #0d140d; border: 1px solid #182418; border-radius: 6px;")
            f_box.setFixedHeight(80)
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

            r_lbl = QLabel(f"{self.i18n.tr('rain_prob')}: {day['rain_chance']}", f_box)
            r_lbl.setAlignment(Qt.AlignCenter)
            r_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 8px; font-family: {FONT_FAMILY};")

            fb_layout.addWidget(d_lbl)
            fb_layout.addWidget(d_ic)
            fb_layout.addWidget(t_lbl)
            fb_layout.addWidget(r_lbl)

            f_row.addWidget(f_box)

        self.main_layout.addLayout(f_row)

        # AI Field Action Advisory (Collapsible)
        if ai_advisory:
            localized_adv_text = self._resolve_advisory_text(ai_advisory)
            is_warn = ai_advisory.get("is_warn", False) if isinstance(ai_advisory, dict) else False

            btn_bg = "#221700" if is_warn else "#0a1e0d"
            btn_border = "#d99000" if is_warn else "#28a745"
            btn_color = "#ffcc00" if is_warn else "#55ff55"
            card_bg = "#140f02" if is_warn else "#061408"

            adv_btn = QPushButton(self)
            title_txt = self.i18n.tr("ai_field_action_advisory")
            click_txt = self.i18n.tr("click_to_view_insights")
            adv_btn.setText(f" ⚠️  {title_txt}  •  {click_txt}  ▼")
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
            adv_card.setVisible(False)

            ac_layout = QHBoxLayout(adv_card)
            ac_layout.setContentsMargins(14, 10, 14, 10)
            ac_layout.setSpacing(0)

            adv_txt = QLabel(localized_adv_text, adv_card)
            adv_txt.setWordWrap(True)
            adv_txt.setStyleSheet(f"color: #f0f0f0; font-size: 12px; font-weight: 500; font-family: {FONT_FAMILY}; line-height: 18px; border: none; background: transparent;")

            ac_layout.addWidget(adv_txt, 1)

            def _toggle_advisory():
                currently_visible = adv_card.isVisible()
                adv_card.setVisible(not currently_visible)
                hide_txt = self.i18n.tr("hide_insights")
                if not currently_visible:
                    adv_btn.setText(f" ⚠️  {title_txt}  •  {hide_txt}  ▲")
                else:
                    adv_btn.setText(f" ⚠️  {title_txt}  •  {click_txt}  ▼")

            adv_btn.clicked.connect(_toggle_advisory)

            self.main_layout.addWidget(adv_btn)
            self.main_layout.addWidget(adv_card)

        # Cloud Radar Header & Widget
        r_hdr = QLabel(self.i18n.tr("live_cloud_coverage_radar_map"), self)
        r_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 700; font-family: {FONT_FAMILY};")
        self.main_layout.addWidget(r_hdr)

        self.radar_widget = CloudRadarWidget(cloud_val, self)
        self.main_layout.addWidget(self.radar_widget, 1)

    def _clear_layout(self, layout):
        """Recursively clear child layout items."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _translate_condition(self, cond: str) -> str:
        mapping = {
            "Sunny": "weather_sunny",
            "Partly Cloudy": "weather_partly_cloudy",
            "Cloudy": "weather_cloudy",
            "Foggy": "weather_foggy",
            "Drizzle": "weather_drizzle",
            "Rainy": "weather_rainy",
            "Rain Showers": "weather_rain_showers",
            "Thunderstorm": "weather_thunderstorm",
        }
        key = mapping.get(cond, "weather_cloudy")
        return self.i18n.tr(key, cond)

    def _translate_leaching(self, leaching_str: str) -> str:
        if "CRITICAL" in leaching_str:
            return leaching_str.replace("CRITICAL", self.i18n.tr("leaching_critical"))
        elif "HIGH" in leaching_str:
            return leaching_str.replace("HIGH", self.i18n.tr("leaching_high"))
        elif "MODERATE" in leaching_str:
            return leaching_str.replace("MODERATE", self.i18n.tr("leaching_moderate"))
        elif "LOW" in leaching_str:
            return leaching_str.replace("LOW", self.i18n.tr("leaching_low"))
        return leaching_str

    def _translate_spray(self, spray_status: str) -> str:
        if spray_status == "OPTIMAL":
            return self.i18n.tr("spray_optimal")
        elif spray_status == "MODERATE":
            return self.i18n.tr("spray_moderate")
        elif spray_status == "UNFAVORABLE":
            return self.i18n.tr("spray_unfavorable")
        return spray_status

    def _resolve_advisory_text(self, ai_advisory) -> str:
        if isinstance(ai_advisory, dict):
            key = ai_advisory.get("key", "adv_favorable")
            params = ai_advisory.get("params", {})
            template = self.i18n.tr(key, ai_advisory.get("text", ""))
            try:
                return template.format(**params)
            except Exception:
                return template
        elif isinstance(ai_advisory, str):
            return ai_advisory
        return ""

    def _on_language_changed(self, lang_code: str):
        """Dynamic signal handler when farmer switches language."""
        self._render_view()
