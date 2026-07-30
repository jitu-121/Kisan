"""
Crop Recommendation Page View for Project KISAN.
Flow: Land size input -> floor(acres * 5) sample calculation -> sensor readings -> ML model inference -> Top 10 Ranked Crops.
"""

import json, math
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from database.db import db_session
from database.models import CropRecommendationSession
from services.recommendation_service import RecommendationService
from services.sensor_service import SensorService
from utils.auth import AuthManager
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
)


class CropRecPage(QWidget):
    """Crop Recommendation Page View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # Top Control Strip: Land size input & trigger
        ctrl_strip = QFrame(self)
        ctrl_strip.setFixedHeight(50)
        ctrl_strip.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 6px;")

        ctrl_layout = QHBoxLayout(ctrl_strip)
        ctrl_layout.setContentsMargins(10, 4, 10, 4)
        ctrl_layout.setSpacing(10)

        lbl = QLabel("Land Size (Acres):", ctrl_strip)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 600;")

        self.acres_input = QLineEdit("1.0", ctrl_strip)
        self.acres_input.setFixedWidth(60)
        self.acres_input.setFixedHeight(28)
        self.acres_input.setStyleSheet("background: #0a0f0a; color: #e5e5e5; border: 1px solid #00d97e; border-radius: 4px; padding: 0 4px;")
        self.acres_input.textChanged.connect(self._update_samples_count)

        self.samples_lbl = QLabel("Required Samples: 5", ctrl_strip)
        self.samples_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 700;")

        self.btn_run = QPushButton("Run Crop Recommendation Model", ctrl_strip)
        self.btn_run.setFixedHeight(32)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setStyleSheet(f"background-color: {COLOR_PRIMARY_ACCENT}; color: #0a0f0a; border-radius: 4px; font-weight: 700; font-size: 11px; padding: 0 10px;")
        self.btn_run.clicked.connect(self._run_recommendation)

        ctrl_layout.addWidget(lbl)
        ctrl_layout.addWidget(self.acres_input)
        ctrl_layout.addWidget(self.samples_lbl)
        ctrl_layout.addStretch(1)
        ctrl_layout.addWidget(self.btn_run)

        layout.addWidget(ctrl_strip)

        # Scrollable Area for Top 10 Predictions
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)

        self.scroll.setWidget(self.results_container)
        layout.addWidget(self.scroll, 1)

        # Initial Run
        self._run_recommendation()

    def _update_samples_count(self):
        try:
            acres = float(self.acres_input.text().strip())
            samples = math.floor(acres * 5)
            self.samples_lbl.setText(f"Required Samples: {max(1, samples)}")
        except ValueError:
            self.samples_lbl.setText("Required Samples: 5")

    def _run_recommendation(self):
        # Clear previous results
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            acres = float(self.acres_input.text().strip())
        except ValueError:
            acres = 1.0

        num_samples = max(1, math.floor(acres * 5))

        # Collect & Average Samples
        samples = [SensorService.read_sensor_data() for _ in range(num_samples)]
        avg_ph = round(sum(s["ph"] if s.get("ph") is not None else 6.8 for s in samples) / num_samples, 1)
        avg_n = round(sum(s["nitrogen"] if s.get("nitrogen") is not None else 75.0 for s in samples) / num_samples, 1)
        avg_p = round(sum(s["phosphorus"] if s.get("phosphorus") is not None else 40.0 for s in samples) / num_samples, 1)
        avg_k = round(sum(s["potassium"] if s.get("potassium") is not None else 180.0 for s in samples) / num_samples, 1)
        avg_m = round(sum(s["moisture"] if s.get("moisture") is not None else 35.0 for s in samples) / num_samples, 1)
        avg_t = round(sum(s["temperature"] if s.get("temperature") is not None else 27.0 for s in samples) / num_samples, 1)


        # Inference
        top_10 = RecommendationService.predict_crops(avg_ph, avg_n, avg_p, avg_k, avg_m, avg_t)

        # 1. Best Match Card
        best = top_10[0]
        best_card = QFrame()
        best_card.setStyleSheet("background-color: #122412; border: 1px solid #00d97e; border-radius: 8px;")
        bc_layout = QHBoxLayout(best_card)
        bc_layout.setContentsMargins(12, 10, 12, 10)

        ic = QLabel(best_card)
        ic.setPixmap(qta.icon(best["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(32, 32))

        b_txt = QVBoxLayout()
        b_title = QLabel(f"RANK #1: {best['crop'].upper()} (BEST SUITED CROP)", best_card)
        b_title.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 14px; font-weight: 800;")

        b_desc = QLabel(f"Confidence Score: {best['confidence']}% • Target Baseline: {best['baseline_npk']}\nAnalyzed vector across {num_samples} soil samples: pH {avg_ph}, N {avg_n}, P {avg_p}, K {avg_k}", best_card)
        b_desc.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px;")

        b_txt.addWidget(b_title)
        b_txt.addWidget(b_desc)

        bc_layout.addWidget(ic)
        bc_layout.addLayout(b_txt, 1)
        self.results_layout.addWidget(best_card)

        # 2. Next 3 Runner-Ups (Ranks 2-4)
        runners_hdr = QLabel("Top Runner-Up Crops:", self.results_container)
        runners_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 700;")
        self.results_layout.addWidget(runners_hdr)

        r_row = QHBoxLayout()
        for idx, crop_data in enumerate(top_10[1:4], start=2):
            rc = QFrame()
            rc.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 6px;")
            rc_l = QVBoxLayout(rc)
            rc_l.setContentsMargins(8, 6, 8, 6)

            r_lbl = QLabel(f"#{idx} {crop_data['crop']}", rc)
            r_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 700;")
            r_sub = QLabel(f"Match: {crop_data['confidence']}%", rc)
            r_sub.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 10px; font-weight: 600;")

            rc_l.addWidget(r_lbl)
            rc_l.addWidget(r_sub)
            r_row.addWidget(rc)

        self.results_layout.addLayout(r_row)

        # 3. Remaining 6 Crops (Ranks 5-10)
        rem_hdr = QLabel("Other Suitable Crops:", self.results_container)
        rem_hdr.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 700;")
        self.results_layout.addWidget(rem_hdr)

        rem_grid = QHBoxLayout()
        for idx, crop_data in enumerate(top_10[4:10], start=5):
            c_box = QFrame()
            c_box.setStyleSheet("background-color: #0d140d; border: 1px solid #142014; border-radius: 4px;")
            c_l = QVBoxLayout(c_box)
            c_l.setContentsMargins(6, 4, 6, 4)

            t_l = QLabel(f"#{idx} {crop_data['crop']}", c_box)
            t_l.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: 600;")
            m_l = QLabel(f"{crop_data['confidence']}%", c_box)
            m_l.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")

            c_l.addWidget(t_l)
            c_l.addWidget(m_l)
            rem_grid.addWidget(c_box)

        self.results_layout.addLayout(rem_grid)

        # Save session to DB if farmer logged in
        farmer = AuthManager.get_current_farmer()
        if farmer:
            sess = CropRecommendationSession(
                farmer_id=farmer.id,
                land_size_acres=acres,
                num_samples_taken=num_samples,
                avg_ph=avg_ph,
                avg_nitrogen=avg_n,
                avg_phosphorus=avg_p,
                avg_potassium=avg_k,
                avg_moisture=avg_m,
                avg_temperature=avg_t,
                model_version_used="v1.2-RF",
                top_10_predictions=json.dumps(top_10)
            )
            db_session.add(sess)
            db_session.commit()
