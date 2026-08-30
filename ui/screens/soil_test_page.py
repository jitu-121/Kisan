"""
Soil Test Page View for Project KISAN.
Uses QStackedWidget for 100% in-page view transitions (NO desktop OS popup dialogs or 'X' cross buttons!).
View 0: 2-Column Soil Analysis Dashboard
View 1: In-Page Full-Screen Field Sampling Wizard View with '⬅ Back to Soil Test' button.
"""

import math
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from database.db import db_session
from database.models import SoilTestSession
from services.sensor_service import SensorService
from utils.auth import AuthManager
from utils.pdf_exporter import PDFExporter
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class SoilTestPage(QWidget):
    """Clean In-Page Soil Analysis Laboratory View with Stacked In-Page Wizard."""
    navigate_to_page = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_acreage_data = None
        self.captured_samples = []
        self.current_spot = 1
        self.req_tests = 5
        self.acres = 1.0
        self._init_ui()

        # Telemetry timer for real-time sensor updates (checks every 2 seconds)
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self._run_realtime_scan)
        self.telemetry_timer.start(2000)

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        self.stack = QStackedWidget(self)

        # ---------------------------------------------------------------------
        # VIEW 0: Main 2-Column Soil Test Dashboard View
        # ---------------------------------------------------------------------
        self.dashboard_view = QWidget(self)
        dash_layout = QHBoxLayout(self.dashboard_view)
        dash_layout.setContentsMargins(12, 10, 12, 10)
        dash_layout.setSpacing(12)

        # Left Column (65%): Sensor Cards
        left_column = QWidget(self.dashboard_view)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        hdr_box = QFrame(left_column)
        hdr_box.setObjectName("HeaderBox")
        hdr_box.setStyleSheet("""
            QFrame#HeaderBox {
                background-color: #0d1424;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QFrame#HeaderBox QLabel {
                border: none;
                background: transparent;
            }
        """)
        hdr_l = QHBoxLayout(hdr_box)
        hdr_l.setContentsMargins(10, 6, 10, 6)

        t_ic = QLabel(hdr_box)
        t_ic.setPixmap(qta.icon("fa5s.vial", color=COLOR_PRIMARY_ACCENT).pixmap(20, 20))

        t_lbl = QLabel("Soil Telemetry Laboratory", hdr_box)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 13px; font-weight: 800;")

        self.status_pill = QLabel(hdr_box)
        self.status_pill.setStyleSheet("""
            QLabel {
                font-family: """ + FONT_FAMILY + """;
                font-size: 10px;
                font-weight: 700;
                border-radius: 10px;
                padding: 3px 8px;
            }
        """)

        btn_scan = QPushButton("  Quick Scan", hdr_box)
        btn_scan.setFixedHeight(28)
        btn_scan.setCursor(Qt.PointingHandCursor)
        btn_scan.setIcon(qta.icon("fa5s.sync", color="#ffffff"))
        btn_scan.setStyleSheet(f"""
            QPushButton {{
                background-color: #14532d;
                color: #ffffff;
                border: 1px solid {COLOR_PRIMARY_ACCENT};
                border-radius: 5px;
                font-family: {FONT_FAMILY};
                font-size: 10px;
                font-weight: 700;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: #166534;
            }}
        """)
        btn_scan.clicked.connect(self._run_single_test)

        hdr_l.addWidget(t_ic)
        hdr_l.addWidget(t_lbl)
        hdr_l.addWidget(self.status_pill)
        hdr_l.addStretch(1)
        hdr_l.addWidget(btn_scan)

        left_layout.addWidget(hdr_box)

        # Grid Container
        grid_container = QWidget(left_column)
        self.cards_grid = QGridLayout(grid_container)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setSpacing(8)

        self.card_widgets = {}
        self._build_sensor_cards()

        left_layout.addWidget(grid_container, 1)

        hw_note = QLabel("Hardware Spec: RS485 Modbus RTU 4800-8-N-1 • /dev/ttyUSB0", left_column)
        hw_note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-style: italic;")
        left_layout.addWidget(hw_note)

        # Right Column (35%): Farm Acreage Hub
        right_column = QFrame(self.dashboard_view)
        right_column.setObjectName("RightPanel")
        right_column.setStyleSheet("""
            QFrame#RightPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #091522, stop:1 #0c1c11);
                border: 1px solid #164e26;
                border-radius: 10px;
            }
            QFrame#RightPanel QLabel {
                border: none;
                background: transparent;
            }
        """)

        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        r_hdr = QHBoxLayout()
        r_ic = QLabel(right_column)
        r_ic.setPixmap(qta.icon("fa5s.seedling", color=COLOR_PRIMARY_ACCENT).pixmap(20, 20))

        r_t_box = QVBoxLayout()
        r_t_box.setSpacing(0)
        r_title = QLabel("Farm Acreage Test Hub", right_column)
        r_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 13px; font-weight: 800;")
        r_sub = QLabel("Multi-Sample Telemetry & PDF Export", right_column)
        r_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")

        r_t_box.addWidget(r_title)
        r_t_box.addWidget(r_sub)

        r_hdr.addWidget(r_ic)
        r_hdr.addLayout(r_t_box, 1)

        right_layout.addLayout(r_hdr)

        div1 = QFrame(right_column)
        div1.setFixedHeight(1)
        div1.setStyleSheet("background-color: #164e26;")
        right_layout.addWidget(div1)

        acre_box = QVBoxLayout()
        acre_box.setSpacing(4)

        a_lbl = QLabel("Select Farm Size (Acres):", right_column)
        a_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 700;")

        spin_row = QHBoxLayout()
        self.spin_acres = QDoubleSpinBox(right_column)
        self.spin_acres.setRange(0.25, 100.0)
        self.spin_acres.setSingleStep(0.25)
        self.spin_acres.setValue(1.0)
        self.spin_acres.setMinimumHeight(32)
        self.spin_acres.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #0b101d;
                color: #ffffff;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: 800;
                font-size: 12px;
            }
        """)
        self.spin_acres.valueChanged.connect(self._on_acres_changed)

        self.req_tests_lbl = QLabel("5 Samples", right_column)
        self.req_tests_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 800;")

        spin_row.addWidget(self.spin_acres, 1)
        spin_row.addWidget(self.req_tests_lbl)

        acre_box.addWidget(a_lbl)
        acre_box.addLayout(spin_row)

        right_layout.addLayout(acre_box)

        formula_txt = QLabel("Formula: 1 Acre = 5 Samples • 0.5 Acre = 3 Samples", right_column)
        formula_txt.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")
        right_layout.addWidget(formula_txt)

        self.btn_run_wizard = QPushButton("🌾 Start Sampling Wizard", right_column)
        self.btn_run_wizard.setFixedHeight(36)
        self.btn_run_wizard.setCursor(Qt.PointingHandCursor)
        self.btn_run_wizard.setStyleSheet(f"""
            QPushButton {{
                background-color: #166534;
                color: #ffffff;
                border: 1px solid {COLOR_PRIMARY_ACCENT};
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 11px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: #22c55e;
                color: #000000;
            }}
        """)
        self.btn_run_wizard.clicked.connect(self._open_in_page_wizard)
        right_layout.addWidget(self.btn_run_wizard)

        self.btn_download_pdf = QPushButton("📥 Download PDF Report", right_column)
        self.btn_download_pdf.setFixedHeight(34)
        self.btn_download_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_download_pdf.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: #ffffff;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                font-family: """ + FONT_FAMILY + """;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_download_pdf.clicked.connect(self._download_pdf_report)
        right_layout.addWidget(self.btn_download_pdf)

        right_layout.addStretch(1)

        self.avg_card = QFrame(right_column)
        self.avg_card.setStyleSheet("background-color: #07140b; border: 1px solid #14381e; border-radius: 6px;")
        ac_l = QVBoxLayout(self.avg_card)
        ac_l.setContentsMargins(8, 6, 8, 6)

        self.avg_results_lbl = QLabel("Select farm size & start wizard to run multi-sample field test.", self.avg_card)
        self.avg_results_lbl.setWordWrap(True)
        self.avg_results_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-style: italic;")

        ac_l.addWidget(self.avg_results_lbl)
        right_layout.addWidget(self.avg_card)

        dash_layout.addWidget(left_column, 65)
        dash_layout.addWidget(right_column, 35)

        # ---------------------------------------------------------------------
        # VIEW 1: Full-Screen In-Page Field Sampling Wizard View (NO Popups!)
        # ---------------------------------------------------------------------
        self.wizard_view = QWidget(self)
        wiz_layout = QVBoxLayout(self.wizard_view)
        wiz_layout.setContentsMargins(14, 10, 14, 10)
        wiz_layout.setSpacing(8)

        # Header Bar with 'Back to Soil Test' Button
        w_hdr = QFrame(self.wizard_view)
        w_hdr.setStyleSheet("background-color: #0d1424; border: 1px solid #1e293b; border-radius: 8px;")
        wh_l = QHBoxLayout(w_hdr)
        wh_l.setContentsMargins(12, 8, 12, 8)

        btn_back = QPushButton("⬅ Back to Soil Laboratory", w_hdr)
        btn_back.setFixedHeight(42)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        btn_back.clicked.connect(self._go_back_to_dashboard)

        self.w_title_lbl = QLabel("🌾 Field Sampling Wizard", w_hdr)
        self.w_title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 800;")

        wh_l.addWidget(btn_back)
        wh_l.addWidget(self.w_title_lbl)
        wh_l.addStretch(1)

        wiz_layout.addWidget(w_hdr)

        # Progress Bar
        self.wiz_prog_bar = QProgressBar(self.wizard_view)
        self.wiz_prog_bar.setFixedHeight(28)
        self.wiz_prog_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0d1424;
                border: 1px solid #1e293b;
                border-radius: 12px;
                text-align: center;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_PRIMARY_ACCENT};
                border-radius: 11px;
            }}
        """)
        wiz_layout.addWidget(self.wiz_prog_bar)

        # Active Spot Card
        self.wiz_spot_card = QFrame(self.wizard_view)
        self.wiz_spot_card.setStyleSheet("background-color: #0d1424; border: 1px solid #1e293b; border-radius: 8px;")
        sc_l = QHBoxLayout(self.wiz_spot_card)
        sc_l.setContentsMargins(16, 10, 16, 10)

        self.wiz_spot_lbl = QLabel("📍 Current Spot: Sample #1 of 5", self.wiz_spot_card)
        self.wiz_spot_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")

        self.wiz_btn_capture = QPushButton("📍 Capture Spot #1 Reading", self.wiz_spot_card)
        self.wiz_btn_capture.setFixedHeight(45)
        self.wiz_btn_capture.setCursor(Qt.PointingHandCursor)
        self.wiz_btn_capture.setIcon(qta.icon("fa5s.vial", color="#ffffff"))
        self.wiz_btn_capture.setStyleSheet(f"""
            QPushButton {{
                background-color: #14532d;
                color: #ffffff;
                border: 1px solid {COLOR_PRIMARY_ACCENT};
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background-color: #166534;
            }}
        """)
        self.wiz_btn_capture.clicked.connect(self._capture_wizard_spot)

        sc_l.addWidget(self.wiz_spot_lbl)
        sc_l.addStretch(1)
        sc_l.addWidget(self.wiz_btn_capture)

        wiz_layout.addWidget(self.wiz_spot_card)

        # Captured Samples Breakdown Table
        self.wiz_table = QTableWidget(0, 7, self.wizard_view)
        self.wiz_table.setHorizontalHeaderLabels(["Spot #", "pH", "Nitrogen", "Phosphorus", "Potassium", "Moisture", "Temp"])
        self.wiz_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wiz_table.horizontalHeader().setMinimumHeight(40)
        self.wiz_table.verticalHeader().setDefaultSectionSize(40) # Larger row height for touch selection
        self.wiz_table.setStyleSheet("""
            QTableWidget {
                background-color: #0b101d;
                color: #ffffff;
                border: 1px solid #141c2e;
                border-radius: 6px;
                gridline-color: #1e293b;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #111a2e;
                color: #22c55e;
                font-weight: 700;
                border: 1px solid #1e293b;
                padding: 8px;
                font-size: 13px;
            }
        """)
        self.wiz_table.setFixedHeight(260) # Increased height to easily fit all rows with larger heights
        wiz_layout.addWidget(self.wiz_table)

        # Finish Action Button (placed just below the table)
        wiz_bot = QHBoxLayout()
        self.wiz_btn_finish = QPushButton("  Complete Field Sampling & Calculate Averages", self.wizard_view)
        self.wiz_btn_finish.setFixedHeight(50)
        self.wiz_btn_finish.setEnabled(False)
        self.wiz_btn_finish.setCursor(Qt.PointingHandCursor)
        self.wiz_btn_finish.setStyleSheet("""
            QPushButton {
                background-color: #166534;
                color: #ffffff;
                border: 1px solid #22c55e;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 800;
                padding: 0 20px;
            }
            QPushButton:disabled {
                background-color: #1b263b;
                color: #64748b;
                border: 1px solid #334155;
            }
        """)
        self.wiz_btn_finish.clicked.connect(self._finish_wizard_sampling)

        wiz_bot.addStretch(1)
        wiz_bot.addWidget(self.wiz_btn_finish)
        wiz_bot.addStretch(1)
        wiz_layout.addLayout(wiz_bot)

        # Add a stretch to push everything compactly to the top
        wiz_layout.addStretch(1)

        # Assemble Stacked Widget Views
        self.stack.addWidget(self.dashboard_view)  # Index 0
        self.stack.addWidget(self.wizard_view)     # Index 1

        page_layout.addWidget(self.stack)

    def _build_sensor_cards(self):
        sensor_specs = [
            ("ph", "pH Level", "fa5s.vial", "#38bdf8", "pH"),
            ("nitrogen", "Nitrogen (N)", "fa5s.seedling", "#22c55e", "kg/hector"),
            ("phosphorus", "Phosphorus (P)", "fa5s.fire", "#f59e0b", "kg/hector"),
            ("potassium", "Potassium (K)", "fa5s.cubes", "#10b981", "kg/hector"),
            ("moisture", "Soil Moisture", "fa5s.water", "#06b6d4", "%"),
            ("temperature", "Soil Temp", "fa5s.thermometer-half", "#f43f5e", "°C"),
        ]

        data = SensorService.read_sensor_data()
        self._update_status(data.get("is_online", False))

        for idx, (key, title_str, icon_name, accent_color, unit_str) in enumerate(sensor_specs):
            card = QFrame(self)
            card.setObjectName("SoilCard")
            card.setStyleSheet("""
                QFrame#SoilCard {
                    background-color: #0d1424;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame#SoilCard QLabel {
                    border: none;
                    background: transparent;
                }
            """)

            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(12, 8, 12, 8)
            c_layout.setSpacing(2)

            top = QHBoxLayout()
            top.setSpacing(8)

            avatar = QFrame(card)
            avatar.setFixedSize(26, 26)
            avatar.setStyleSheet(f"""
                QFrame {{
                    background-color: #131d33;
                    border: 1px solid {accent_color};
                    border-radius: 13px;
                }}
                QFrame QLabel {{
                    border: none;
                    background: transparent;
                }}
            """)
            av_l = QVBoxLayout(avatar)
            av_l.setContentsMargins(0, 0, 0, 0)
            av_l.setAlignment(Qt.AlignCenter)

            av_ic = QLabel(avatar)
            av_ic.setPixmap(qta.icon(icon_name, color=accent_color).pixmap(14, 14))
            av_l.addWidget(av_ic)

            t_lbl = QLabel(title_str, card)
            t_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 600;")

            top.addWidget(avatar)
            top.addWidget(t_lbl, 1)

            val_box = QHBoxLayout()
            val_box.setSpacing(4)
            val_box.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            val_str = data["display_values"].get(key, "--")
            val_lbl = QLabel(val_str, card)
            val_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 900;")

            unit_lbl = QLabel(unit_str if data.get("is_online", False) else "", card)
            unit_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 500;")

            val_box.addWidget(val_lbl)
            val_box.addWidget(unit_lbl)
            val_box.addStretch(1)

            sub_str = f"Status: {data['tags'][key]}" if data.get("is_online", False) else ""
            sub_lbl = QLabel(sub_str, card)
            sub_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 9px; font-weight: 600;")

            c_layout.addLayout(top)
            c_layout.addLayout(val_box)
            c_layout.addWidget(sub_lbl)

            row, col = divmod(idx, 3)
            self.cards_grid.addWidget(card, row, col)
            self.card_widgets[key] = (val_lbl, sub_lbl, unit_lbl, unit_str)

    def _calc_required_tests(self, acres: float) -> int:
        if acres <= 0.5:
            return 3
        return math.ceil(acres * 5)

    def _on_acres_changed(self, val: float):
        req_tests = self._calc_required_tests(val)
        self.req_tests_lbl.setText(f"{req_tests} Samples")

    def _run_single_test(self):
        data = SensorService.read_sensor_data()
        is_online = data.get("is_online", False)
        self._update_status(is_online)

        for key in ["ph", "nitrogen", "phosphorus", "potassium", "moisture", "temperature"]:
            val_lbl, sub_lbl, unit_lbl, unit_str = self.card_widgets[key]
            val_str = data["display_values"].get(key, "--")
            val_lbl.setText(val_str)

            if is_online:
                unit_lbl.setText(unit_str)
                sub_lbl.setText(f"Status: {data['tags'][key]}")
            else:
                unit_lbl.setText("")
                sub_lbl.setText("")

    def _run_realtime_scan(self):
        if not self.isVisible() or self.stack.currentIndex() != 0:
            return
        self._run_single_test()

    def _go_back_to_dashboard(self):
        self.stack.setCurrentIndex(0)
        self.telemetry_timer.start(2000)

    def _open_in_page_wizard(self):
        self.telemetry_timer.stop() # Stop automatic telemetry updates during sampling
        self.acres = self.spin_acres.value()
        self.req_tests = self._calc_required_tests(self.acres)
        self.captured_samples = []
        self.current_spot = 1

        self.w_title_lbl.setText(f"🌾 Field Sampling Wizard — {self.acres} Acres ({self.req_tests} Samples Required)")
        self.wiz_prog_bar.setRange(0, self.req_tests)
        self.wiz_prog_bar.setValue(0)

        self.wiz_spot_lbl.setText(f"📍 Current Spot: Sample #1 of {self.req_tests} — Move probe to spot #1")
        self.wiz_btn_capture.setText("📍 Capture Spot #1 Reading")
        self.wiz_btn_capture.setEnabled(True)
        self.wiz_btn_finish.setEnabled(False)

        self.wiz_table.setRowCount(0)

        # Switch to View 1 (Wizard View)
        self.stack.setCurrentIndex(1)

    def _capture_wizard_spot(self):
        if self.current_spot > self.req_tests:
            return

        sample_data = SensorService.read_sensor_data()
        sample_data["spot_num"] = self.current_spot
        self.captured_samples.append(sample_data)

        r = self.wiz_table.rowCount()
        self.wiz_table.insertRow(r)

        is_online = sample_data.get("is_online", False)
        ph_str = f"{sample_data['ph']:.1f}" if is_online else "--"
        n_str = f"{sample_data['nitrogen']:.0f} kg/hector" if is_online else "--"
        p_str = f"{sample_data['phosphorus']:.0f} kg/hector" if is_online else "--"
        k_str = f"{sample_data['potassium']:.0f} kg/hector" if is_online else "--"
        m_str = f"{sample_data['moisture']:.1f} %" if is_online else "--"
        t_str = f"{sample_data['temperature']:.1f} °C" if is_online else "--"

        vals = [f"Spot #{self.current_spot}", ph_str, n_str, p_str, k_str, m_str, t_str]
        for col, v in enumerate(vals):
            item = QTableWidgetItem(v)
            item.setTextAlignment(Qt.AlignCenter)
            self.wiz_table.setItem(r, col, item)

        self.wiz_prog_bar.setValue(self.current_spot)

        if self.current_spot < self.req_tests:
            self.current_spot += 1
            self.wiz_spot_lbl.setText(f"📍 Current Spot: Sample #{self.current_spot} of {self.req_tests} — Move probe to spot #{self.current_spot}")
            self.wiz_btn_capture.setText(f"📍 Capture Spot #{self.current_spot} Reading")
        else:
            self.wiz_spot_lbl.setText(f"🎉 All {self.req_tests} Probe Samples Captured Successfully!")
            self.wiz_btn_capture.setEnabled(False)
            self.wiz_btn_finish.setEnabled(True)

    def _finish_wizard_sampling(self):
        samples = self.captured_samples
        is_online = any(s.get("is_online", False) for s in samples)
        self._update_status(is_online)

        avg_ph = round(sum(s["ph"] if s.get("ph") is not None else 6.8 for s in samples) / self.req_tests, 2)
        avg_n = round(sum(s["nitrogen"] if s.get("nitrogen") is not None else 75.0 for s in samples) / self.req_tests, 1)
        avg_p = round(sum(s["phosphorus"] if s.get("phosphorus") is not None else 40.0 for s in samples) / self.req_tests, 1)
        avg_k = round(sum(s["potassium"] if s.get("potassium") is not None else 180.0 for s in samples) / self.req_tests, 1)
        avg_m = round(sum(s["moisture"] if s.get("moisture") is not None else 35.0 for s in samples) / self.req_tests, 1)
        avg_t = round(sum(s["temperature"] if s.get("temperature") is not None else 27.0 for s in samples) / self.req_tests, 1)

        avg_tags = {
            "ph": SensorService.get_qualitative_tag("ph", avg_ph),
            "nitrogen": SensorService.get_qualitative_tag("nitrogen", avg_n),
            "phosphorus": SensorService.get_qualitative_tag("phosphorus", avg_p),
            "potassium": SensorService.get_qualitative_tag("potassium", avg_k),
            "moisture": SensorService.get_qualitative_tag("moisture", avg_m),
            "temperature": SensorService.get_qualitative_tag("temperature", avg_t),
        }

        self.current_acreage_data = {
            "acres": self.acres,
            "num_samples": self.req_tests,
            "samples": samples,
            "avg": {
                "ph": avg_ph,
                "nitrogen": avg_n,
                "phosphorus": avg_p,
                "potassium": avg_k,
                "moisture": avg_m,
                "temperature": avg_t,
                "tags": avg_tags
            }
        }

        disp_map = {
            "ph": (f"{avg_ph:.2f}", "pH"),
            "nitrogen": (f"{avg_n:.1f}", "kg/hector"),
            "phosphorus": (f"{avg_p:.1f}", "kg/hector"),
            "potassium": (f"{avg_k:.1f}", "kg/hector"),
            "moisture": (f"{avg_m:.1f}", "%"),
            "temperature": (f"{avg_t:.1f}", "°C"),
        }

        for key in ["ph", "nitrogen", "phosphorus", "potassium", "moisture", "temperature"]:
            val_lbl, sub_lbl, unit_lbl, _ = self.card_widgets[key]
            v_val, v_unit = disp_map[key]
            val_lbl.setText(v_val if is_online else "--")
            unit_lbl.setText(v_unit if is_online else "")
            sub_lbl.setText(f"Field Avg: {avg_tags[key]}" if is_online else "")

        summary_txt = f"Acreage Scan Complete ({self.acres} Acre, {self.req_tests} Samples):\nAvg pH {avg_ph:.1f} • N {avg_n:.0f} • P {avg_p:.0f} • K {avg_k:.0f}"
        self.avg_results_lbl.setText(summary_txt)
        self.avg_results_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 10px; font-weight: 700;")

        # Switch back to View 0 (Dashboard View)
        self.stack.setCurrentIndex(0)
        self.telemetry_timer.start(2000)

    def _download_pdf_report(self):
        if not self.current_acreage_data:
            acres = self.spin_acres.value()
            req_tests = self._calc_required_tests(acres)
            samples = [SensorService.read_sensor_data() for _ in range(req_tests)]
            avg_ph = round(sum(s["ph"] if s.get("ph") is not None else 6.8 for s in samples) / req_tests, 2)
            avg_n = round(sum(s["nitrogen"] if s.get("nitrogen") is not None else 75.0 for s in samples) / req_tests, 1)
            avg_p = round(sum(s["phosphorus"] if s.get("phosphorus") is not None else 40.0 for s in samples) / req_tests, 1)
            avg_k = round(sum(s["potassium"] if s.get("potassium") is not None else 180.0 for s in samples) / req_tests, 1)
            avg_m = round(sum(s["moisture"] if s.get("moisture") is not None else 35.0 for s in samples) / req_tests, 1)
            avg_t = round(sum(s["temperature"] if s.get("temperature") is not None else 27.0 for s in samples) / req_tests, 1)

            avg_tags = {
                "ph": SensorService.get_qualitative_tag("ph", avg_ph),
                "nitrogen": SensorService.get_qualitative_tag("nitrogen", avg_n),
                "phosphorus": SensorService.get_qualitative_tag("phosphorus", avg_p),
                "potassium": SensorService.get_qualitative_tag("potassium", avg_k),
                "moisture": SensorService.get_qualitative_tag("moisture", avg_m),
                "temperature": SensorService.get_qualitative_tag("temperature", avg_t),
            }
            self.current_acreage_data = {
                "acres": acres,
                "num_samples": req_tests,
                "samples": samples,
                "avg": {
                    "ph": avg_ph,
                    "nitrogen": avg_n,
                    "phosphorus": avg_p,
                    "potassium": avg_k,
                    "moisture": avg_m,
                    "temperature": avg_t,
                    "tags": avg_tags
                }
            }

        data = self.current_acreage_data
        pdf_path = PDFExporter.export_acreage_report(
            acres=data["acres"],
            num_samples=data["num_samples"],
            samples_data=data["samples"],
            avg_data=data["avg"],
            farmer_name="Kisan Farmer"
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("PDF Report Exported")
        msg_box.setText(f"Acreage Soil Analysis Report PDF Generated!\n\nFile Location:\n{pdf_path}")
        msg_box.setIcon(QMessageBox.Information)

        btn_go_downloads = msg_box.addButton("Go to Downloads Tab", QMessageBox.ActionRole)
        msg_box.addButton(QMessageBox.Ok)

        msg_box.exec_()

        if msg_box.clickedButton() == btn_go_downloads:
            self.navigate_to_page.emit(6)

    def _update_status(self, is_online: bool):
        if is_online:
            self.status_pill.setText("● PROBE ONLINE")
            self.status_pill.setStyleSheet(f"""
                QLabel {{
                    background-color: #0b2e16;
                    color: {COLOR_PRIMARY_ACCENT};
                    border: 1px solid #166534;
                    border-radius: 10px;
                    padding: 3px 8px;
                }}
            """)
        else:
            self.status_pill.setText("● PROBE OFFLINE")
            self.status_pill.setStyleSheet("""
                QLabel {
                    background-color: #2e0b0b;
                    color: #ef5350;
                    border: 1px solid #651616;
                    border-radius: 10px;
                    padding: 3px 8px;
                }
            """)
