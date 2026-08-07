"""
Crop Recommendation Page View for Project KISAN.
Implements a 3-State Spatial Sampling Wizard in PyQt5:
State 1: Vertical list of 5 reading slots with large touch targets.
State 2: The Processing Phase (UX Fake loading with QTimer).
State 3: The Result Phase with massive bold sensor value grids and highlighted crop card.
"""

import json
import random
import numpy as np
from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QGridLayout,
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
)

# Color Scheme as specified in guidelines / requirements
SLATE_DARK = "#0F172A"
EMERALD_GREEN = "#2E7D32"
EMERALD_LIGHT = "#4ADE80"


class CropRecPage(QWidget):
    """
    3-State Wizard Crop Recommendation Page with Premium Touch Hierarchy.
    Handles spatial soil averaging and ML inference.
    """
    navigate_to_page = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = [None] * 5  # Stores 5 arrays of [N, P, K, pH, Moisture, Temp]
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        # Root layout with 20px margin all around (breathing room)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(0)

        # Main stacked container to swap frames
        self.stack = QStackedWidget(self)
        root_layout.addWidget(self.stack)

        # Build individual State Views
        self._build_state_1_view()
        self._build_state_2_view()
        self._build_state_3_view()

        # Start at State 1
        self.reset_wizard()

    # -------------------------------------------------------------------------
    # STATE 1: Sampling Phase (Data Collection)
    # -------------------------------------------------------------------------
    def _build_state_1_view(self):
        self.view_state_1 = QWidget(self)
        layout = QVBoxLayout(self.view_state_1)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)  # We will use explicit addSpacing for precise padding control
        layout.setAlignment(Qt.AlignTop)

        # Header reading
        self.lbl_s1_header = QLabel("Field Sampling in Progress", self.view_state_1)
        self.lbl_s1_header.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 20px; font-weight: 800;"
        )
        self.lbl_s1_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_s1_header)
        layout.addSpacing(16)  # Space below header

        # Vertical rows for readings
        self.btn_captures = []
        self.lbl_telemetry = []

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
            row_frame.setFixedHeight(48)  # Larger touch-friendly height
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(14, 0, 14, 0)
            row_layout.setSpacing(12)

            lbl_name = QLabel(f"Reading Spot {i+1}:", row_frame)
            lbl_name.setFixedWidth(130)
            lbl_name.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-family: {FONT_FAMILY}; font-size: 14px; font-weight: 800;")

            btn_cap = QPushButton("Capture", row_frame)
            btn_cap.setFixedSize(85, 30)  # Slightly larger button height
            btn_cap.setCursor(Qt.PointingHandCursor)
            btn_cap.setStyleSheet(f"""
                QPushButton {{
                    background-color: {EMERALD_GREEN};
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-family: {FONT_FAMILY};
                    font-size: 13px;
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
            lbl_data.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 14px; font-weight: 600;")

            row_layout.addWidget(lbl_name)
            row_layout.addWidget(btn_cap)
            row_layout.addWidget(lbl_data, 1)

            layout.addWidget(row_frame)
            self.btn_captures.append(btn_cap)
            self.lbl_telemetry.append(lbl_data)

            if i < 4:
                layout.addSpacing(12)  # Breathing space between slot frames

        layout.addSpacing(22)  # Breathing space above Predict Crop button

        # Large Action Predict Button (50px height for finger tapping)
        self.btn_predict = QPushButton("Predict Crop", self.view_state_1)
        self.btn_predict.setFixedHeight(50)
        self.btn_predict.setFixedWidth(240)
        self.btn_predict.setCursor(Qt.PointingHandCursor)
        self.btn_predict.setStyleSheet(f"""
            QPushButton {{
                background-color: {EMERALD_GREEN};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 16px;
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
        # Fetch current sensor telemetry
        data = SensorService.read_sensor_data()
        
        # If offline or invalid, mock realistic data
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

        # Save this slot reading
        self.samples[idx] = [n, p, k, ph, moisture, temp]

        # Update Slot Preview Label
        self.lbl_telemetry[idx].setText(
            f"N: {int(n)} | P: {int(p)} | K: {int(k)} | pH: {ph} | Temp: {temp}°C | Moist: {moisture}%"
        )
        self.lbl_telemetry[idx].setStyleSheet(f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 700;")
        self.btn_captures[idx].setText("Re-Capture")

        # Enable the next slot's capture button
        if idx + 1 < 5:
            self.btn_captures[idx + 1].setEnabled(True)

        # Check if all 5 spots have been sampled
        if all(s is not None for s in self.samples):
            self.btn_predict.setEnabled(True)

    # -------------------------------------------------------------------------
    # STATE 2: Processing Phase (UX Polish / Loading Screen)
    # -------------------------------------------------------------------------
    def _build_state_2_view(self):
        self.view_state_2 = QWidget(self)
        layout = QVBoxLayout(self.view_state_2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        # Centered loading animation/text
        self.lbl_s2_status = QLabel("Processing data...", self.view_state_2)
        self.lbl_s2_status.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 18px; font-weight: 700;"
        )
        self.lbl_s2_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_s2_status)

        self.stack.addWidget(self.view_state_2)

    def _transition_to_processing(self):
        self.stack.setCurrentIndex(1)
        
        # Step A: Perform numerical average instantly using numpy.mean
        # self.samples is [ [N, P, K, pH, Moisture, Temp], ... ]
        self.averaged_vector = np.mean(self.samples, axis=0)

        # Phase 1: Average message
        self.lbl_s2_status.setText("Averaging 5 spatial soil samples...")

        # Phase 2 delay: 1.0 second -> Load AI model message
        QTimer.singleShot(1000, self._step2_loading_model)

    def _step2_loading_model(self):
        self.lbl_s2_status.setText("Loading Edge-AI inference model...")
        
        # Phase 3 delay: 1.5 seconds -> Predict crop and show Result page
        QTimer.singleShot(1500, self._step2_run_inference)

    def _step2_run_inference(self):
        avg_n, avg_p, avg_k, avg_ph, avg_m, avg_t = self.averaged_vector

        # Predict top 10 recommended crops
        top_10 = RecommendationService.predict_crops(
            ph=round(avg_ph, 1),
            n=round(avg_n, 1),
            p=round(avg_p, 1),
            k=round(avg_k, 1),
            moisture=round(avg_m, 1),
            temp=round(avg_t, 1)
        )

        best_crop = top_10[0]
        
        self.lbl_s3_prediction.setText(best_crop['crop'].upper())
        self.lbl_s3_confidence.setText(f"Confidence Score  {best_crop['confidence']:.1f} %")
        self.lbl_best_icon.setPixmap(qta.icon(best_crop['icon'], color=EMERALD_LIGHT).pixmap(32, 32))

        # Update Runner cards
        for idx in range(3):
            if idx + 1 < len(top_10):
                crop_data = top_10[idx + 1]
                self.runner_names[idx].setText(crop_data['crop'].upper())
                self.runner_pcts[idx].setText(f"{crop_data['confidence']:.1f}%")
                self.runner_icons[idx].setPixmap(qta.icon(crop_data['icon'], color=EMERALD_LIGHT).pixmap(20, 20))

        # Update the massive telemetry labels inside the grid
        self.lbl_grid_vals["N"].setText(str(int(avg_n)))
        self.lbl_grid_vals["P"].setText(str(int(avg_p)))
        self.lbl_grid_vals["K"].setText(str(int(avg_k)))
        self.lbl_grid_vals["pH"].setText(str(round(avg_ph, 1)))
        self.lbl_grid_vals["Moisture"].setText(f"{int(avg_m)}%")
        self.lbl_grid_vals["Temp"].setText(f"{int(avg_t)}°C")

        # Save session to DB if farmer is authenticated
        farmer = AuthManager.get_current_farmer()
        if farmer:
            sess = CropRecommendationSession(
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
                top_10_predictions=json.dumps(top_10)
            )
            db_session.add(sess)
            db_session.commit()

        # Switch to State 3
        self.stack.setCurrentIndex(2)

    # -------------------------------------------------------------------------
    # STATE 3: Result Phase (Output Screen)
    # -------------------------------------------------------------------------
    def _build_state_3_view(self):
        self.view_state_3 = QWidget(self)
        layout = QVBoxLayout(self.view_state_3)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        # Unified 560px centered column container to prevent misalignment and clipping
        center_widget = QWidget(self.view_state_3)
        center_widget.setFixedWidth(560)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # 1. Best Match Card Container
        best_match_frame = QFrame(center_widget)
        best_match_frame.setObjectName("BestMatchFrame")
        best_match_frame.setStyleSheet("""
            QFrame#BestMatchFrame {
                background: transparent;
                border: none;
            }
        """)
        best_match_frame.setFixedHeight(94)
        
        bm_layout = QHBoxLayout(best_match_frame)
        bm_layout.setContentsMargins(0, 0, 0, 0)
        bm_layout.setSpacing(18)
        
        # Left circular icon badge
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
        
        # Right details layout
        details_layout = QVBoxLayout()
        details_layout.setSpacing(3)
        details_layout.setAlignment(Qt.AlignVCenter)
        
        lbl_bm_title = QLabel("Best Match", best_match_frame)
        lbl_bm_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 700; border: none; background: transparent;")
        
        self.lbl_s3_prediction = QLabel("SUGARCANE", best_match_frame)
        self.lbl_s3_prediction.setStyleSheet(f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 26px; font-weight: 800; border: none; background: transparent;")
        
        # Confidence pill
        self.pill_frame = QFrame(best_match_frame)
        self.pill_frame.setObjectName("PillFrame")
        self.pill_frame.setFixedHeight(24)
        self.pill_frame.setFixedWidth(210)
        self.pill_frame.setStyleSheet(f"""
            QFrame#PillFrame {{
                border: 1px solid #16a34a;
                border-radius: 12px;
                background-color: #0b1511;
            }}
        """)
        pill_layout = QHBoxLayout(self.pill_frame)
        pill_layout.setContentsMargins(12, 0, 12, 0)
        self.lbl_s3_confidence = QLabel("Confidence Score  92.4 %", self.pill_frame)
        self.lbl_s3_confidence.setStyleSheet(f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        pill_layout.addWidget(self.lbl_s3_confidence, 0, Qt.AlignCenter)
        
        details_layout.addWidget(lbl_bm_title)
        details_layout.addWidget(self.lbl_s3_prediction)
        details_layout.addWidget(self.pill_frame)
        
        bm_layout.addLayout(details_layout, 1)
        center_layout.addWidget(best_match_frame)

        center_layout.addSpacing(16)

        # 2. Runner-ups Layout (Header + Cards)
        lbl_runners_header = QLabel("Other Suitable Crops", center_widget)
        lbl_runners_header.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 700;")
        center_layout.addWidget(lbl_runners_header)

        center_layout.addSpacing(6)

        # Horizontal layout for the 3 runner cards (centered exactly within the 560px column)
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
            card.setFixedSize(177, 94)  # Expanded slightly to fill 560px width nicely
            
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(8, 10, 8, 10)
            c_lay.setSpacing(4)
            c_lay.setAlignment(Qt.AlignCenter)
            
            ic = QLabel(card)
            ic.setFixedSize(24, 24)
            ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet("border: none; background: transparent;")
            
            nm = QLabel("JOWAR", card)
            nm.setAlignment(Qt.AlignCenter)
            nm.setStyleSheet(f"color: #ffffff; font-family: {FONT_FAMILY}; font-size: 11px; font-weight: 800; border: none; background: transparent;")
            
            pt = QLabel("74.6%", card)
            pt.setAlignment(Qt.AlignCenter)
            pt.setStyleSheet(f"color: {EMERALD_LIGHT}; font-family: {FONT_FAMILY}; font-size: 10px; font-weight: 700; border: none; background: transparent;")
            
            c_lay.addWidget(ic)
            c_lay.addWidget(nm)
            c_lay.addWidget(pt)
            
            self.runners_layout.addWidget(card)
            self.runner_icons.append(ic)
            self.runner_names.append(nm)
            self.runner_pcts.append(pt)
            
        center_layout.addWidget(runners_widget)

        center_layout.addSpacing(16)

        # 3. Compact Telemetry Grid
        grid_frame = QFrame(center_widget)
        grid_frame.setStyleSheet("background-color: #0b1329; border: 1px solid #1e293b; border-radius: 8px;")
        grid_frame.setFixedHeight(64)
        
        grid_layout = QHBoxLayout(grid_frame)
        grid_layout.setContentsMargins(8, 4, 8, 4)
        grid_layout.setSpacing(8)

        parameters = [
            ("N", "Nitrogen"),
            ("P", "Phosphorus"),
            ("K", "Potassium"),
            ("pH", "pH Level"),
            ("Moisture", "Moisture"),
            ("Temp", "Temperature"),
        ]

        self.lbl_grid_vals = {}

        for key, name in parameters:
            cell = QFrame(grid_frame)
            cell.setStyleSheet("background-color: #0f172a; border-radius: 5px;")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(4, 2, 4, 2)
            cell_layout.setSpacing(1)
            cell_layout.setAlignment(Qt.AlignCenter)

            val_lbl = QLabel("--", cell)
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet(f"color: #ffffff; font-family: {FONT_FAMILY}; font-size: 16px; font-weight: 800;")
            
            name_lbl = QLabel(name, cell)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"color: #94a3b8; font-family: {FONT_FAMILY}; font-size: 8px; font-weight: 600;")

            cell_layout.addWidget(val_lbl)
            cell_layout.addWidget(name_lbl)
            grid_layout.addWidget(cell)

            self.lbl_grid_vals[key] = val_lbl

        center_layout.addWidget(grid_frame)
        center_layout.addSpacing(16)

        # 4. Bottom Buttons (50px tall touch targets)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignCenter)

        # Button 1: Calculate Fertilizer Deficit
        self.btn_fertilizer = QPushButton("Calculate Fertilizer Deficit", self.view_state_3)
        self.btn_fertilizer.setFixedHeight(50)
        self.btn_fertilizer.setFixedWidth(240)
        self.btn_fertilizer.setCursor(Qt.PointingHandCursor)
        self.btn_fertilizer.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-family: """ + FONT_FAMILY + """;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_fertilizer.clicked.connect(self._calculate_fertilizer)
        btn_layout.addWidget(self.btn_fertilizer)

        # Button 2: Start New Scan
        self.btn_new_scan = QPushButton("Start New Scan", self.view_state_3)
        self.btn_new_scan.setFixedHeight(50)
        self.btn_new_scan.setFixedWidth(160)
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

        center_layout.addLayout(btn_layout)

        # Add the entire centered layout column to the main view layout
        layout.addWidget(center_widget, 0, Qt.AlignCenter)
        self.stack.addWidget(self.view_state_3)

    def _calculate_fertilizer(self):
        print("[Crop Recommendation] Calculate Fertilizer Deficit Action Triggered!")
        # Emit page switch signal to Fertilizer Recommendation Page (Index 3 in SidebarIdx)
        self.navigate_to_page.emit(3)

    # -------------------------------------------------------------------------
    # RESET AND INITIALIZATION
    # -------------------------------------------------------------------------
    def reset_wizard(self):
        """Reset sampling parameters and return UI to State 1."""
        self.samples = [None] * 5
        
        # Reset telemetry strings & button states
        for i in range(5):
            self.lbl_telemetry[i].setText("N: -- | P: -- | K: -- | pH: -- | Temp: -- | Moist: --")
            self.lbl_telemetry[i].setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 600;")
            self.btn_captures[i].setText("Capture")
            # Only enable the first slot initially
            self.btn_captures[i].setEnabled(i == 0)

        # Predict Crop is disabled until all 5 slots are populated
        self.btn_predict.setEnabled(False)
        self.stack.setCurrentIndex(0)

