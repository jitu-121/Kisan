"""
Crop Recommendation Page View for Project KISAN.
Implements a 3-State Spatial Sampling Wizard with Stage 1 ML + Stage 2 MCDA Economic Engine.
Full Native Multi-Language i18n Support (English, Hindi, Marathi).
"""

import json
import random
import numpy as np
from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from database.db import db_session
from database.models import CropRecommendationSession, EconomicRecommendationSession
from services.economic_service import EconomicService
from services.recommendation_service import RecommendationService
from services.sensor_service import SensorService
from utils.auth import AuthManager
from utils.i18n import get_language_manager
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)

SLATE_DARK = "#0F172A"
EMERALD_GREEN = "#2E7D32"
EMERALD_LIGHT = "#4ADE80"


class CostBreakdownDialog(QDialog):
    """Popup Dialog displaying itemized cultivation & soil remediation costs."""

    def __init__(self, crop_data: dict, parent=None):
        super().__init__(parent)
        self.crop_data = crop_data
        self.i18n = get_language_manager()
        self.setWindowTitle(f"{self.i18n.tr('cost_breakdown_title')} - {crop_data['crop'].upper()}")
        self.setFixedSize(450, 390)
        self.setStyleSheet(f"background-color: #0f172a; color: #ffffff; font-family: {FONT_FAMILY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(f"{self.i18n.tr('cost_breakdown_title')}: {crop_data['crop'].upper()}", self)
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #4ADE80;")
        layout.addWidget(title)

        breakdown = crop_data.get("cost_breakdown", {})

        grid = QGridLayout()
        grid.setSpacing(10)

        items = [
            (self.i18n.tr("seeds_cost"), f"Rs. {breakdown.get('seeds', 0):,.2f}"),
            (self.i18n.tr("labor_cost"), f"Rs. {breakdown.get('labor', 0):,.2f}"),
            (self.i18n.tr("irrigation_cost"), f"Rs. {breakdown.get('irrigation', 0):,.2f}"),
            (self.i18n.tr("pesticides_cost"), f"Rs. {breakdown.get('pesticides', 0):,.2f}"),
            (self.i18n.tr("remediation_cost"), f"Rs. {breakdown.get('remediation', 0):,.2f}"),
        ]

        for idx, (label_text, val_text) in enumerate(items):
            lbl_k = QLabel(label_text, self)
            lbl_k.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600;")
            lbl_v = QLabel(val_text, self)
            lbl_v.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700;")
            lbl_v.setAlignment(Qt.AlignRight)
            grid.addWidget(lbl_k, idx, 0)
            grid.addWidget(lbl_v, idx, 1)

        layout.addLayout(grid)

        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #334155;")
        layout.addWidget(line)

        total_layout = QHBoxLayout()
        lbl_tot_k = QLabel(self.i18n.tr("total_cultivation_cost"), self)
        lbl_tot_k.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800;")
        lbl_tot_v = QLabel(f"Rs. {crop_data.get('c_total_per_acre', 0):,.2f}", self)
        lbl_tot_v.setStyleSheet("color: #f59e0b; font-size: 15px; font-weight: 800;")
        lbl_tot_v.setAlignment(Qt.AlignRight)
        total_layout.addWidget(lbl_tot_k)
        total_layout.addWidget(lbl_tot_v)
        layout.addLayout(total_layout)

        btn_close = QPushButton(self.i18n.tr("close"), self)
        btn_close.setFixedHeight(40)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {EMERALD_GREEN};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 13px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: #1e5e22;
            }}
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class CropRecPage(QWidget):
    """
    3-State Wizard Crop Recommendation Page with Dual-View Stage 1 ML & Stage 2 MCDA Economic Engine.
    Fully localized in English, Hindi, and Marathi.
    """

    navigate_to_page = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = [None] * 5
        self.economic_service = EconomicService()
        self.current_economic_results = []
        self.i18n = get_language_manager()
        self._init_ui()

        # Connect language change signal
        self.i18n.language_changed.connect(self._on_language_changed)

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(15, 15, 15, 15)
        root_layout.setSpacing(0)

        self.stack = QStackedWidget(self)
        root_layout.addWidget(self.stack)

        self._build_state_1_view()
        self._build_state_2_view()
        self._build_state_3_view()

        self.reset_wizard()

    # -------------------------------------------------------------------------
    # STATE 1: Sampling Phase (Data Collection)
    # -------------------------------------------------------------------------
    def _build_state_1_view(self):
        self.view_state_1 = QWidget(self)
        layout = QVBoxLayout(self.view_state_1)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        self.lbl_s1_header = QLabel(self.i18n.tr("field_sampling_in_progress"), self.view_state_1)
        self.lbl_s1_header.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 20px; font-weight: 800;"
        )
        self.lbl_s1_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_s1_header)
        layout.addSpacing(16)

        self.btn_captures = []
        self.lbl_telemetry = []
        self.lbl_spot_names = []

        for i in range(5):
            row_frame = QFrame(self.view_state_1)
            row_frame.setObjectName(f"RowFrame_{i}")
            row_frame.setStyleSheet(f"""
                QFrame#RowFrame_{i} {{
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }}
            """)
            row_frame.setFixedHeight(48)
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(14, 0, 14, 0)
            row_layout.setSpacing(12)

            lbl_name = QLabel(f"{self.i18n.tr('reading_spot')} {i+1}:", row_frame)
            lbl_name.setFixedWidth(140)
            lbl_name.setStyleSheet(
                f"color: {COLOR_PRIMARY_ACCENT}; font-family: {FONT_FAMILY}; font-size: 13px; font-weight: 800;"
            )
            self.lbl_spot_names.append(lbl_name)

            btn_cap = QPushButton(self.i18n.tr("capture"), row_frame)
            btn_cap.setFixedSize(95, 30)
            btn_cap.setCursor(Qt.PointingHandCursor)
            btn_cap.setStyleSheet(f"""
                QPushButton {{
                    background-color: {EMERALD_GREEN};
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-family: {FONT_FAMILY};
                    font-size: 12px;
                    font-weight: 800;
                }}
                QPushButton:disabled {{
                    background-color: #334155;
                    color: #94a3b8;
                }}
                QPushButton:hover {{
                    background-color: #1e5e22;
                }}
            """)
            btn_cap.clicked.connect(lambda checked, idx=i: self._capture_specific_reading(idx))

            lbl_data = QLabel("N: -- | P: -- | K: -- | pH: -- | Temp: -- | Moist: --", row_frame)
            lbl_data.setStyleSheet(
                f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 14px; font-weight: 600;"
            )

            row_layout.addWidget(lbl_name)
            row_layout.addWidget(btn_cap)
            row_layout.addWidget(lbl_data, 1)

            layout.addWidget(row_frame)
            self.btn_captures.append(btn_cap)
            self.lbl_telemetry.append(lbl_data)

            if i < 4:
                layout.addSpacing(12)

        layout.addSpacing(22)

        self.btn_predict = QPushButton(self.i18n.tr("predict_crop_analyze_economy"), self.view_state_1)
        self.btn_predict.setFixedHeight(50)
        self.btn_predict.setFixedWidth(340)
        self.btn_predict.setCursor(Qt.PointingHandCursor)
        self.btn_predict.setStyleSheet(f"""
            QPushButton {{
                background-color: {EMERALD_GREEN};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 15px;
                font-weight: 800;
            }}
            QPushButton:disabled {{
                background-color: #334155;
                color: #64748b;
            }}
            QPushButton:hover {{
                background-color: #1e5e22;
            }}
        """)
        self.btn_predict.clicked.connect(self._transition_to_processing)
        layout.addWidget(self.btn_predict, 0, Qt.AlignCenter)

        self.stack.addWidget(self.view_state_1)

    def _capture_specific_reading(self, idx: int):
        data = SensorService.read_sensor_data()

        if not data.get("is_online", False):
            n = float(random.randint(60, 110))
            p = float(random.randint(30, 60))
            k = float(random.randint(120, 220))
            ph = round(random.uniform(6.2, 7.4), 1)
            moisture = float(random.randint(28, 48))
            temp = float(random.randint(24, 30))
        else:
            n = float(data.get("nitrogen", 75.0))
            p = float(data.get("phosphorus", 40.0))
            k = float(data.get("potassium", 180.0))
            ph = float(data.get("ph", 6.8))
            moisture = float(data.get("moisture", 35.0))
            temp = float(data.get("temperature", 27.0))

        self.samples[idx] = [n, p, k, ph, moisture, temp]

        self.lbl_telemetry[idx].setText(
            f"N: {int(n)} | P: {int(p)} | K: {int(k)} | pH: {ph} | Temp: {temp}°C | Moist: {moisture}%"
        )
        self.lbl_telemetry[idx].setStyleSheet(
            f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 700;"
        )
        self.btn_captures[idx].setText(self.i18n.tr("recapture"))

        if idx + 1 < 5:
            self.btn_captures[idx + 1].setEnabled(True)

        if all(s is not None for s in self.samples):
            self.btn_predict.setEnabled(True)

    # -------------------------------------------------------------------------
    # STATE 2: Processing Phase
    # -------------------------------------------------------------------------
    def _build_state_2_view(self):
        self.view_state_2 = QWidget(self)
        layout = QVBoxLayout(self.view_state_2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_s2_status = QLabel("Processing data...", self.view_state_2)
        self.lbl_s2_status.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 18px; font-weight: 700;"
        )
        self.lbl_s2_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_s2_status)

        self.stack.addWidget(self.view_state_2)

    def _transition_to_processing(self):
        self.stack.setCurrentIndex(1)
        self.averaged_vector = np.mean(self.samples, axis=0)
        self.lbl_s2_status.setText(self.i18n.tr("field_sampling_in_progress"))
        QTimer.singleShot(600, self._step2_loading_model)

    def _step2_loading_model(self):
        self.lbl_s2_status.setText(self.i18n.tr("predict_crop_analyze_economy"))
        QTimer.singleShot(800, self._step2_run_inference)

    def _step2_run_inference(self):
        avg_n, avg_p, avg_k, avg_ph, avg_m, avg_t = self.averaged_vector

        top_10 = RecommendationService.predict_crops(
            ph=round(avg_ph, 1),
            n=round(avg_n, 1),
            p=round(avg_p, 1),
            k=round(avg_k, 1),
            moisture=round(avg_m, 1),
            temp=round(avg_t, 1),
        )

        best_crop = top_10[0]
        self.lbl_s3_prediction.setText(best_crop["crop"].upper())
        self.lbl_s3_confidence.setText(f"{self.i18n.tr('confidence_score')}  {best_crop['confidence']:.1f} %")
        self.lbl_best_icon.setPixmap(qta.icon(best_crop["icon"], color=EMERALD_LIGHT).pixmap(32, 32))

        for idx in range(3):
            if idx + 1 < len(top_10):
                crop_data = top_10[idx + 1]
                self.runner_names[idx].setText(crop_data["crop"].upper())
                self.runner_pcts[idx].setText(f"{crop_data['confidence']:.1f}%")
                self.runner_icons[idx].setPixmap(
                    qta.icon(crop_data["icon"], color=EMERALD_LIGHT).pixmap(20, 20)
                )

        self.current_economic_results = self.economic_service.calculate_economic_ranking(
            soil_n=round(avg_n, 1),
            soil_p=round(avg_p, 1),
            soil_k=round(avg_k, 1),
            land_acres=1.0,
            stage1_recommendations=top_10,
        )

        self._populate_financial_tab(self.current_economic_results)

        self.lbl_grid_vals["N"].setText(str(int(avg_n)))
        self.lbl_grid_vals["P"].setText(str(int(avg_p)))
        self.lbl_grid_vals["K"].setText(str(int(avg_k)))
        self.lbl_grid_vals["pH"].setText(str(round(avg_ph, 1)))
        self.lbl_grid_vals["Moisture"].setText(f"{int(avg_m)}%")
        self.lbl_grid_vals["Temp"].setText(f"{int(avg_t)}°C")

        farmer = AuthManager.get_current_farmer()
        if farmer:
            sess_ml = CropRecommendationSession(
                farmer_id=farmer.id,
                land_size_acres=1.0,
                num_samples_taken=5,
                avg_ph=round(avg_ph, 1),
                avg_nitrogen=round(avg_n, 1),
                avg_phosphorus=round(avg_p, 1),
                avg_potassium=round(avg_k, 1),
                avg_moisture=round(avg_m, 1),
                avg_temperature=round(avg_t, 1),
                model_version_used="v1.2-RF",
                top_10_predictions=json.dumps(top_10),
            )
            db_session.add(sess_ml)

            if self.current_economic_results:
                best_econ = self.current_economic_results[0]
                sess_econ = EconomicRecommendationSession(
                    farmer_id=farmer.id,
                    land_size_acres=1.0,
                    selected_crop=best_econ["crop"],
                    expected_yield=best_econ["y_expected_per_acre"],
                    total_cost=best_econ["c_total_per_acre"],
                    remediation_cost=best_econ["c_remediation_per_acre"],
                    estimated_harvest_price=best_econ["p_effective"],
                    net_profit=best_econ["net_profit_per_acre"],
                    roi_percentage=best_econ["roi_percent"],
                    prescriptive_score=best_econ["s_prescriptive"],
                    msp_backed=best_econ["msp_backed"],
                    all_economic_rankings=json.dumps(self.current_economic_results),
                )
                db_session.add(sess_econ)

            db_session.commit()

        self.stack.setCurrentIndex(2)

    # -------------------------------------------------------------------------
    # STATE 3: Result Phase (Dual-View Tabs Layout)
    # -------------------------------------------------------------------------
    def _build_state_3_view(self):
        self.view_state_3 = QWidget(self)
        layout = QVBoxLayout(self.view_state_3)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)

        self.tab_widget = QTabWidget(self.view_state_3)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #1e293b;
                border-radius: 8px;
                background-color: #0b1329;
            }}
            QTabBar::tab {{
                background-color: #0f172a;
                color: #94a3b8;
                font-family: {FONT_FAMILY};
                font-size: 13px;
                font-weight: 700;
                padding: 10px 24px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {EMERALD_GREEN};
                color: #ffffff;
                font-weight: 800;
            }}
            QTabBar::tab:hover {{
                background-color: #1e293b;
                color: #ffffff;
            }}
        """)

        self._build_tab_1_agronomic()
        self._build_tab_2_financial()

        self.tab_widget.addTab(self.tab_1_widget, self.i18n.tr("biological_suitability_tab"))
        self.tab_widget.addTab(self.tab_2_widget, self.i18n.tr("prescriptive_financial_tab"))

        layout.addWidget(self.tab_widget, 1)

        grid_frame = QFrame(self.view_state_3)
        grid_frame.setStyleSheet("background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px;")
        grid_frame.setFixedHeight(54)

        grid_layout = QHBoxLayout(grid_frame)
        grid_layout.setContentsMargins(6, 2, 6, 2)
        grid_layout.setSpacing(6)

        self.param_keys = [
            ("N", "nitrogen"),
            ("P", "phosphorus"),
            ("K", "potassium"),
            ("pH", "ph_level"),
            ("Moisture", "moisture"),
            ("Temp", "temperature"),
        ]

        self.lbl_grid_vals = {}
        self.lbl_grid_names = {}
        for key, i18n_k in self.param_keys:
            cell = QFrame(grid_frame)
            cell.setStyleSheet("background-color: #1e293b; border-radius: 4px;")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(4, 2, 4, 2)
            cell_layout.setSpacing(1)
            cell_layout.setAlignment(Qt.AlignCenter)

            val_lbl = QLabel("--", cell)
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet(
                f"color: #ffffff; font-family: {FONT_FAMILY}; font-size: 14px; font-weight: 800;"
            )

            name_lbl = QLabel(self.i18n.tr(i18n_k), cell)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(
                f"color: #94a3b8; font-family: {FONT_FAMILY}; font-size: 8px; font-weight: 600;"
            )

            cell_layout.addWidget(val_lbl)
            cell_layout.addWidget(name_lbl)
            grid_layout.addWidget(cell)

            self.lbl_grid_vals[key] = val_lbl
            self.lbl_grid_names[key] = name_lbl

        layout.addWidget(grid_frame)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_fertilizer = QPushButton(self.i18n.tr("calculate_fertilizer_deficit"), self.view_state_3)
        self.btn_fertilizer.setFixedHeight(44)
        self.btn_fertilizer.setFixedWidth(260)
        self.btn_fertilizer.setCursor(Qt.PointingHandCursor)
        self.btn_fertilizer.setStyleSheet(f"""
            QPushButton {{
                background-color: #1d4ed8;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 13px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """)
        self.btn_fertilizer.clicked.connect(self._calculate_fertilizer)
        btn_layout.addWidget(self.btn_fertilizer)

        self.btn_new_scan = QPushButton(self.i18n.tr("start_new_scan"), self.view_state_3)
        self.btn_new_scan.setFixedHeight(44)
        self.btn_new_scan.setFixedWidth(180)
        self.btn_new_scan.setCursor(Qt.PointingHandCursor)
        self.btn_new_scan.setStyleSheet(f"""
            QPushButton {{
                background-color: {EMERALD_GREEN};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 13px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: #1e5e22;
            }}
        """)
        self.btn_new_scan.clicked.connect(self.reset_wizard)
        btn_layout.addWidget(self.btn_new_scan)

        layout.addLayout(btn_layout)
        self.stack.addWidget(self.view_state_3)

    # -------------------------------------------------------------------------
    # TAB 1: Biological Suitability View
    # -------------------------------------------------------------------------
    def _build_tab_1_agronomic(self):
        self.tab_1_widget = QWidget()
        layout = QVBoxLayout(self.tab_1_widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        center_widget = QWidget(self.tab_1_widget)
        center_widget.setFixedWidth(560)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)

        best_match_frame = QFrame(center_widget)
        best_match_frame.setObjectName("BestMatchFrame")
        best_match_frame.setStyleSheet("QFrame#BestMatchFrame { background: transparent; border: none; }")
        best_match_frame.setFixedHeight(94)

        bm_layout = QHBoxLayout(best_match_frame)
        bm_layout.setContentsMargins(0, 0, 0, 0)
        bm_layout.setSpacing(18)

        self.lbl_best_icon = QLabel(best_match_frame)
        self.lbl_best_icon.setFixedSize(64, 64)
        self.lbl_best_icon.setAlignment(Qt.AlignCenter)
        self.lbl_best_icon.setStyleSheet(f"""
            QLabel {{
                border: 3px solid {EMERALD_LIGHT};
                border-radius: 32px;
                background-color: #0b1a11;
            }}
        """)
        bm_layout.addWidget(self.lbl_best_icon, 0, Qt.AlignVCenter)

        details_layout = QVBoxLayout()
        details_layout.setSpacing(3)
        details_layout.setAlignment(Qt.AlignVCenter)

        self.lbl_bm_title = QLabel(self.i18n.tr("best_biological_match"), best_match_frame)
        self.lbl_bm_title.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 700;"
        )

        self.lbl_s3_prediction = QLabel("SUGARCANE", best_match_frame)
        self.lbl_s3_prediction.setStyleSheet(
            f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 26px; font-weight: 800;"
        )

        self.pill_frame = QFrame(best_match_frame)
        self.pill_frame.setObjectName("PillFrame")
        self.pill_frame.setFixedHeight(24)
        self.pill_frame.setFixedWidth(230)
        self.pill_frame.setStyleSheet("""
            QFrame#PillFrame {
                border: 1px solid #16a34a;
                border-radius: 12px;
                background-color: #0b1511;
            }
        """)
        pill_layout = QHBoxLayout(self.pill_frame)
        pill_layout.setContentsMargins(12, 0, 12, 0)
        self.lbl_s3_confidence = QLabel(f"{self.i18n.tr('confidence_score')}  92.4 %", self.pill_frame)
        self.lbl_s3_confidence.setStyleSheet(
            f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 11px; font-weight: 700;"
        )
        pill_layout.addWidget(self.lbl_s3_confidence, 0, Qt.AlignCenter)

        details_layout.addWidget(self.lbl_bm_title)
        details_layout.addWidget(self.lbl_s3_prediction)
        details_layout.addWidget(self.pill_frame)

        bm_layout.addLayout(details_layout, 1)
        center_layout.addWidget(best_match_frame)

        self.lbl_runners_header = QLabel(self.i18n.tr("other_suitable_crops"), center_widget)
        self.lbl_runners_header.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 700;"
        )
        center_layout.addWidget(self.lbl_runners_header)

        runners_widget = QWidget(center_widget)
        self.runners_layout = QHBoxLayout(runners_widget)
        self.runners_layout.setContentsMargins(0, 0, 0, 0)
        self.runners_layout.setSpacing(14)

        self.runner_icons = []
        self.runner_names = []
        self.runner_pcts = []

        for i in range(3):
            card = QFrame(runners_widget)
            card.setObjectName(f"RunnerCard_{i}")
            card.setStyleSheet(f"""
                QFrame#RunnerCard_{i} {{
                    background-color: #09130d;
                    border: 1px solid #165328;
                    border-radius: 8px;
                }}
            """)
            card.setFixedSize(177, 90)

            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(8, 8, 8, 8)
            c_lay.setSpacing(4)
            c_lay.setAlignment(Qt.AlignCenter)

            ic = QLabel(card)
            ic.setFixedSize(24, 24)
            ic.setAlignment(Qt.AlignCenter)

            nm = QLabel("RICE", card)
            nm.setAlignment(Qt.AlignCenter)
            nm.setStyleSheet(
                f"color: #ffffff; font-family: {FONT_FAMILY}; font-size: 11px; font-weight: 800;"
            )

            pt = QLabel("74.6%", card)
            pt.setAlignment(Qt.AlignCenter)
            pt.setStyleSheet(
                f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 10px; font-weight: 700;"
            )

            c_lay.addWidget(ic)
            c_lay.addWidget(nm)
            c_lay.addWidget(pt)

            self.runners_layout.addWidget(card)
            self.runner_icons.append(ic)
            self.runner_names.append(nm)
            self.runner_pcts.append(pt)

        center_layout.addWidget(runners_widget)
        layout.addWidget(center_widget, 0, Qt.AlignCenter)

    # -------------------------------------------------------------------------
    # TAB 2: Prescriptive Financial View
    # -------------------------------------------------------------------------
    def _build_tab_2_financial(self):
        self.tab_2_widget = QWidget()
        layout = QVBoxLayout(self.tab_2_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        scroll_area = QScrollArea(self.tab_2_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.cards_container)
        layout.addWidget(scroll_area)

    def _populate_financial_tab(self, economic_results: list):
        """Dynamically populate Tab 2 with localized economic cards."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not economic_results:
            lbl_empty = QLabel("No economic data available.", self.cards_container)
            lbl_empty.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 700;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(lbl_empty)
            return

        for idx, econ in enumerate(economic_results[:5]):
            card = QFrame(self.cards_container)
            card.setStyleSheet("""
                QFrame {
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 1px solid #2E7D32;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(8)

            top_row = QHBoxLayout()
            top_row.setSpacing(10)

            lbl_rank = QLabel(f"#{idx+1}", card)
            lbl_rank.setStyleSheet(
                f"color: {EMERALD_LIGHT}; font-size: 16px; font-weight: 800;"
            )

            lbl_crop_name = QLabel(econ["crop"].upper(), card)
            lbl_crop_name.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 800;")

            lbl_score = QLabel(f"Prescriptive Score: {econ['s_prescriptive']:.1f} / 100", card)
            lbl_score.setStyleSheet(
                "background-color: #1e293b; color: #38bdf8; font-size: 11px; font-weight: 800; padding: 4px 8px; border-radius: 4px;"
            )

            top_row.addWidget(lbl_rank)
            top_row.addWidget(lbl_crop_name)
            top_row.addWidget(lbl_score)

            if econ.get("msp_backed", 0):
                lbl_msp = QLabel(self.i18n.tr("msp_protected"), card)
                lbl_msp.setStyleSheet(
                    "background-color: #064e3b; color: #34d399; font-size: 11px; font-weight: 800; padding: 4px 8px; border-radius: 4px;"
                )
                top_row.addWidget(lbl_msp)

            top_row.addStretch()
            card_layout.addLayout(top_row)

            metrics_grid = QGridLayout()
            metrics_grid.setSpacing(8)

            metrics = [
                (self.i18n.tr("expected_net_profit"), f"Rs. {econ['net_profit_per_acre']:,.2f} / acre", "#4ADE80"),
                (self.i18n.tr("return_on_investment"), f"{econ['roi_percent']:.1f} %", "#f59e0b"),
                (self.i18n.tr("est_harvest_price"), f"Rs. {econ['p_effective']:,.2f} / Qtl", "#e2e8f0"),
                (self.i18n.tr("expected_yield"), f"{econ['y_expected_per_acre']:.1f} Qtl / acre", "#e2e8f0"),
            ]

            for m_idx, (m_title, m_val, color_hex) in enumerate(metrics):
                lbl_t = QLabel(m_title, card)
                lbl_t.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
                lbl_v = QLabel(m_val, card)
                lbl_v.setStyleSheet(f"color: {color_hex}; font-size: 14px; font-weight: 800;")
                metrics_grid.addWidget(lbl_t, 0, m_idx)
                metrics_grid.addWidget(lbl_v, 1, m_idx)

            card_layout.addLayout(metrics_grid)

            bot_row = QHBoxLayout()
            bot_row.addStretch()

            btn_breakdown = QPushButton(self.i18n.tr("view_cost_breakdown"), card)
            btn_breakdown.setFixedHeight(30)
            btn_breakdown.setFixedWidth(180)
            btn_breakdown.setCursor(Qt.PointingHandCursor)
            btn_breakdown.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #cbd5e1;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #ffffff;
                }
            """)
            btn_breakdown.clicked.connect(
                lambda checked, data=econ: self._open_cost_breakdown(data)
            )
            bot_row.addWidget(btn_breakdown)

            card_layout.addLayout(bot_row)
            self.cards_layout.addWidget(card)

    def _open_cost_breakdown(self, crop_data: dict):
        dialog = CostBreakdownDialog(crop_data, self)
        dialog.exec_()

    def _on_language_changed(self, lang_code: str):
        """Dynamic signal handler when farmer switches language."""
        self.lbl_s1_header.setText(self.i18n.tr("field_sampling_in_progress"))
        for i in range(5):
            self.lbl_spot_names[i].setText(f"{self.i18n.tr('reading_spot')} {i+1}:")
            if self.samples[i] is not None:
                self.btn_captures[i].setText(self.i18n.tr("recapture"))
            else:
                self.btn_captures[i].setText(self.i18n.tr("capture"))

        self.btn_predict.setText(self.i18n.tr("predict_crop_analyze_economy"))
        self.tab_widget.setTabText(0, self.i18n.tr("biological_suitability_tab"))
        self.tab_widget.setTabText(1, self.i18n.tr("prescriptive_financial_tab"))

        self.lbl_bm_title.setText(self.i18n.tr("best_biological_match"))
        self.lbl_runners_header.setText(self.i18n.tr("other_suitable_crops"))
        self.btn_fertilizer.setText(self.i18n.tr("calculate_fertilizer_deficit"))
        self.btn_new_scan.setText(self.i18n.tr("start_new_scan"))

        for key, i18n_k in self.param_keys:
            if key in self.lbl_grid_names:
                self.lbl_grid_names[key].setText(self.i18n.tr(i18n_k))

        if self.current_economic_results:
            self._populate_financial_tab(self.current_economic_results)

    def _calculate_fertilizer(self):
        print("[Crop Recommendation] Calculate Fertilizer Deficit Action Triggered!")
        self.navigate_to_page.emit(3)

    # -------------------------------------------------------------------------
    # RESET AND INITIALIZATION
    # -------------------------------------------------------------------------
    def reset_wizard(self):
        self.samples = [None] * 5
        self.current_economic_results = []

        for i in range(5):
            self.lbl_telemetry[i].setText("N: -- | P: -- | K: -- | pH: -- | Temp: -- | Moist: --")
            self.lbl_telemetry[i].setStyleSheet(
                f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 600;"
            )
            self.btn_captures[i].setText(self.i18n.tr("capture"))
            self.btn_captures[i].setEnabled(i == 0)

        self.btn_predict.setEnabled(False)
        self.stack.setCurrentIndex(0)
