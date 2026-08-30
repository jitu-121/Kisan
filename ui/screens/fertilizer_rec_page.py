"""
Fertilizer Recommendation Page View for Project KISAN.
In-Page 2-View Architecture (QStackedWidget):
- View 0: Dedicated Full-Width Input Hub (State, District, Crop, Soil Telemetry parameters).
- View 1: Dedicated Full-Width Prediction & Dosage Schedule Dashboard.
"""

import re
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from services.fertilizer_service import FertilizerService
from services.sensor_service import SensorService
from ui.custom_combo_box import CustomTouchComboBox
from utils.pdf_exporter import PDFExporter
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


def _clean_crop_display(name_str: str, comb_str: str = "") -> str:
    """Clean crop display name to present English-first clear text."""
    name_clean = str(name_str or "Crop").strip().title()
    comb_clean = str(comb_str or "").strip()

    if not comb_clean or comb_clean.startswith("(") or comb_clean.lower() in ["rabi", "kharif", "all variety"]:
        return name_clean

    if "/" in comb_clean:
        for p in reversed(comb_clean.split("/")):
            p_s = p.strip()
            if re.search(r'[a-zA-Z]', p_s) and len(p_s) > 2:
                return p_s.title()

    eng_words = re.findall(r'[a-zA-Z0-9\s]+', comb_clean)
    eng_text = " ".join([w.strip() for w in eng_words if len(w.strip()) > 1]).title()

    if eng_text and eng_text.lower() not in ["all variety", "rabi", "kharif"]:
        return f"{name_clean} ({eng_text})"

    return name_clean


def _get_fertilizer_icon(name_str: str) -> str:
    """Return appropriate icon for fertilizer name."""
    n = name_str.lower()
    if "urea" in n:
        return "fa5s.vial"
    elif "dap" in n or "ssp" in n or "phosphate" in n:
        return "fa5s.cubes"
    elif "mop" in n or "potash" in n:
        return "fa5s.gem"
    elif "fym" in n or "manure" in n or "compost" in n:
        return "fa5s.leaf"
    elif "bio" in n or "jeevamrut" in n:
        return "fa5s.seedling"
    elif "cake" in n or "neem" in n:
        return "fa5s.tree"
    return "fa5s.flask"


class FertilizerRecPage(QWidget):
    """Touchscreen Fertilizer Recommendation View with Dedicated Input and Prediction Views."""
    navigate_to_page = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.states_list = []
        self.districts_list = []
        self.crops_list = []
        self.current_rec_result = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(0)

        # In-Page Stacked Widget
        self.stack = QStackedWidget(self)
        main_layout.addWidget(self.stack)

        # ---------------------------------------------------------------------
        # VIEW 0: Dedicated Full-Width Input Hub
        # ---------------------------------------------------------------------
        self.view_input = QFrame(self)
        self.view_input.setObjectName("InputPanel")
        self.view_input.setStyleSheet("""
            QFrame#InputPanel {
                background-color: #0d1424;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QFrame#InputPanel QLabel {
                border: none;
                background: transparent;
            }
        """)

        v_inp_layout = QVBoxLayout(self.view_input)
        v_inp_layout.setContentsMargins(18, 14, 18, 14)
        v_inp_layout.setSpacing(12)

        # Input View Header
        hdr = QHBoxLayout()
        ic = QLabel(self.view_input)
        ic.setPixmap(qta.icon("fa5s.prescription-bottle-alt", color=COLOR_PRIMARY_ACCENT).pixmap(24, 24))

        t_box = QVBoxLayout()
        t_box.setSpacing(0)
        title = QLabel("Fertilizer Guidance Calculator - Soil Parameters Input", self.view_input)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 14px; font-weight: 800;")
        sub = QLabel("Official Soil Health Portal Integration (soilhealth.dac.gov.in)", self.view_input)
        sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9.5px;")

        t_box.addWidget(title)
        t_box.addWidget(sub)

        hdr.addWidget(ic)
        hdr.addLayout(t_box, 1)

        v_inp_layout.addLayout(hdr)

        div1 = QFrame(self.view_input)
        div1.setFixedHeight(1)
        div1.setStyleSheet("background-color: #1e293b;")
        v_inp_layout.addWidget(div1)

        # 2-Column Spacious Inputs Layout
        cols_box = QHBoxLayout()
        cols_box.setSpacing(20)

        # Left Column: Location & Target Crop
        col_left = QVBoxLayout()
        col_left.setSpacing(10)

        loc_lbl = QLabel("1. Location & Crop Parameters", self.view_input)
        loc_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 800;")

        st_lbl = QLabel("State:", self.view_input)
        st_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: 700;")
        self.combo_state = CustomTouchComboBox("State", self.view_input)

        dt_lbl = QLabel("District:", self.view_input)
        dt_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: 700;")
        self.combo_district = CustomTouchComboBox("District", self.view_input)

        crop_lbl = QLabel("Target Crop:", self.view_input)
        crop_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: 700;")
        self.combo_crop = CustomTouchComboBox("Target Crop", self.view_input)

        self.chk_natural = QCheckBox("🌱 Natural / Organic Farming Recommendation", self.view_input)
        self.chk_natural.setStyleSheet(f"""
            QCheckBox {{
                background: transparent;
                color: {COLOR_PRIMARY_ACCENT};
                font-size: 10.5px;
                font-weight: 600;
                padding: 6px 0;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                background-color: #0b101d;
                border: 1px solid #166534;
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: #22c55e;
                border: 1px solid #22c55e;
            }}
        """)

        col_left.addWidget(loc_lbl)
        col_left.addWidget(st_lbl)
        col_left.addWidget(self.combo_state)
        col_left.addWidget(dt_lbl)
        col_left.addWidget(self.combo_district)
        col_left.addWidget(crop_lbl)
        col_left.addWidget(self.combo_crop)
        col_left.addWidget(self.chk_natural)
        col_left.addStretch(1)

        # Right Column: Telemetry Parameters
        col_right = QVBoxLayout()
        col_right.setSpacing(10)

        tele_hdr = QHBoxLayout()
        tele_lbl = QLabel("2. Soil Telemetry Parameters", self.view_input)
        tele_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 800;")

        btn_autofill = QPushButton("  Auto-Fill Sensor Data", self.view_input)
        btn_autofill.setFixedHeight(26)
        btn_autofill.setCursor(Qt.PointingHandCursor)
        btn_autofill.setIcon(qta.icon("fa5s.download", color=COLOR_PRIMARY_ACCENT))
        btn_autofill.setStyleSheet(f"""
            QPushButton {{
                background-color: #0b2e16;
                color: {COLOR_PRIMARY_ACCENT};
                border: 1px solid #166534;
                border-radius: 4px;
                font-size: 9.5px;
                font-weight: 700;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: #166534;
                color: #ffffff;
            }}
        """)
        btn_autofill.clicked.connect(self._autofill_probe_data)

        tele_hdr.addWidget(tele_lbl)
        tele_hdr.addStretch(1)
        tele_hdr.addWidget(btn_autofill)

        col_right.addLayout(tele_hdr)

        inputs_grid = QGridLayout()
        inputs_grid.setSpacing(8)

        self.input_n = self._create_line_input("Nitrogen (N) [e.g. 75]")
        self.input_p = self._create_line_input("Phosphorus (P) [e.g. 40]")
        self.input_k = self._create_line_input("Potassium (K) [e.g. 180]")
        self.input_ph = self._create_line_input("pH Level [e.g. 6.8]")
        self.input_oc = self._create_line_input("Organic Carbon [e.g. 0.5%]")

        lbl_n = QLabel("Nitrogen N (kg/hector):", self.view_input)
        lbl_n.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600;")
        lbl_p = QLabel("Phosphorus P (kg/hector):", self.view_input)
        lbl_p.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600;")
        lbl_k = QLabel("Potassium K (kg/hector):", self.view_input)
        lbl_k.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600;")
        lbl_ph = QLabel("pH Level (1-14):", self.view_input)
        lbl_ph.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600;")
        lbl_oc = QLabel("Organic Carbon OC (%):", self.view_input)
        lbl_oc.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600;")

        inputs_grid.addWidget(lbl_n, 0, 0)
        inputs_grid.addWidget(self.input_n, 0, 1)
        inputs_grid.addWidget(lbl_p, 1, 0)
        inputs_grid.addWidget(self.input_p, 1, 1)

        inputs_grid.addWidget(lbl_k, 2, 0)
        inputs_grid.addWidget(self.input_k, 2, 1)
        inputs_grid.addWidget(lbl_ph, 3, 0)
        inputs_grid.addWidget(self.input_ph, 3, 1)

        inputs_grid.addWidget(lbl_oc, 4, 0)
        inputs_grid.addWidget(self.input_oc, 4, 1)

        col_right.addLayout(inputs_grid)
        col_right.addStretch(1)

        cols_box.addLayout(col_left, 1)
        cols_box.addLayout(col_right, 1)

        v_inp_layout.addLayout(cols_box)

        # Action Button (placed in the middle/under inputs and centered)
        calc_btn_layout = QHBoxLayout()
        btn_calc = QPushButton("💊 Calculate Fertilizer Guidance ➔", self.view_input)
        btn_calc.setFixedHeight(54)
        btn_calc.setMinimumWidth(320)
        btn_calc.setCursor(Qt.PointingHandCursor)
        btn_calc.setStyleSheet(f"""
            QPushButton {{
                background-color: #14532d;
                color: #ffffff;
                border: 2px solid {COLOR_PRIMARY_ACCENT};
                border-radius: 8px;
                font-family: {FONT_FAMILY};
                font-size: 15px;
                font-weight: 800;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background-color: #166534;
            }}
        """)
        btn_calc.clicked.connect(self._run_calculation_and_show_results)

        calc_btn_layout.addStretch(1)
        calc_btn_layout.addWidget(btn_calc)
        calc_btn_layout.addStretch(1)

        v_inp_layout.addLayout(calc_btn_layout)

        # Add vertical stretch at the bottom to group inputs and action button compactly in the middle/upper view
        v_inp_layout.addStretch(1)

        self.stack.addWidget(self.view_input)

        # ---------------------------------------------------------------------
        # VIEW 1: Dedicated Full-Width Prediction & Guidance Dashboard
        # ---------------------------------------------------------------------
        self.view_output = QFrame(self)
        self.view_output.setObjectName("OutputPanel")
        self.view_output.setStyleSheet("""
            QFrame#OutputPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #091522, stop:1 #0c1c11);
                border: 1px solid #164e26;
                border-radius: 10px;
            }
            QFrame#OutputPanel QLabel {
                border: none;
                background: transparent;
            }
        """)

        v_out_layout = QVBoxLayout(self.view_output)
        v_out_layout.setContentsMargins(16, 12, 16, 12)
        v_out_layout.setSpacing(8)

        # Header Bar
        r_hdr = QHBoxLayout()

        btn_back_input = QPushButton("⬅ Back to Soil Parameters", self.view_output)
        btn_back_input.setFixedHeight(30)
        btn_back_input.setCursor(Qt.PointingHandCursor)
        btn_back_input.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 5px;
                font-size: 10.5px;
                font-weight: 700;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        btn_back_input.clicked.connect(self._show_input_view)

        r_title = QLabel("Fertilizer Dosage & Application Schedule", self.view_output)
        r_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: 13px; font-weight: 800;")

        self.source_pill = QLabel(self.view_output)
        self.source_pill.setStyleSheet("""
            QLabel {
                font-size: 8.5px;
                font-weight: 700;
                border-radius: 8px;
                padding: 2px 8px;
            }
        """)

        r_hdr.addWidget(btn_back_input)
        r_hdr.addWidget(r_title, 1)
        r_hdr.addWidget(self.source_pill)

        v_out_layout.addLayout(r_hdr)

        div2 = QFrame(self.view_output)
        div2.setFixedHeight(1)
        div2.setStyleSheet("background-color: #164e26;")
        v_out_layout.addWidget(div2)

        # Scrollable Output Container (NO Horizontal Scrollbars!)
        scroll = QScrollArea(self.view_output)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.output_container = QWidget()
        self.output_layout = QVBoxLayout(self.output_container)
        self.output_layout.setContentsMargins(0, 0, 0, 0)
        self.output_layout.setSpacing(10)

        scroll.setWidget(self.output_container)
        v_out_layout.addWidget(scroll, 1)

        # Bottom Action Bar
        bot_bar = QHBoxLayout()

        btn_back_bot = QPushButton("⬅ Back to Inputs", self.view_output)
        btn_back_bot.setFixedHeight(34)
        btn_back_bot.setCursor(Qt.PointingHandCursor)
        btn_back_bot.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        btn_back_bot.clicked.connect(self._show_input_view)

        self.btn_download_pdf = QPushButton("📥 Download Fertilizer Schedule PDF", self.view_output)
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

        bot_bar.addWidget(btn_back_bot)
        bot_bar.addWidget(self.btn_download_pdf, 1)

        v_out_layout.addLayout(bot_bar)

        self.stack.addWidget(self.view_output)

        # Load initial locations & crops
        self._populate_locations_and_crops()

    def _create_line_input(self, placeholder: str) -> QLineEdit:
        inp = QLineEdit(self)
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(30)
        inp.setStyleSheet("""
            QLineEdit {
                background-color: #0b101d;
                color: #ffffff;
                border: 1px solid #1e293b;
                border-radius: 5px;
                padding: 2px 8px;
                font-size: 10.5px;
                font-weight: 600;
            }
            QLineEdit:focus {
                border: 1px solid #22c55e;
            }
        """)
        return inp

    def _show_input_view(self):
        """Switch to View 0 (Input Parameters Hub)."""
        self.stack.setCurrentIndex(0)

    def _populate_locations_and_crops(self):
        self.states_list = FertilizerService.get_states()
        self.combo_state.clear()
        for s in self.states_list:
            self.combo_state.addItem(s["name"], s["id"])

        self.combo_state.currentIndexChanged.connect(self._on_state_changed)
        self.combo_district.currentIndexChanged.connect(self._on_district_changed)

        if self.states_list:
            self.combo_state.setCurrentIndex(0)
            self._on_state_changed(0)

    def _on_state_changed(self, idx: int):
        if idx < 0 or idx >= len(self.states_list):
            return
        state_id = self.states_list[idx]["id"]

        self.districts_list = FertilizerService.get_districts(state_id)
        self.combo_district.clear()
        for d in self.districts_list:
            self.combo_district.addItem(d["name"], d["id"])

        if self.districts_list:
            self.combo_district.setCurrentIndex(0)
            self._on_district_changed(0)

    def _on_district_changed(self, idx: int):
        state_idx = self.combo_state.currentIndex()
        if state_idx < 0 or idx < 0 or idx >= len(self.districts_list):
            return
        state_id = self.states_list[state_idx]["id"]
        district_id = self.districts_list[idx]["id"]

        self.crops_list = FertilizerService.get_crops(state_id, district_id)
        self.combo_crop.clear()
        for c in self.crops_list:
            clean_name = _clean_crop_display(c.get("name"), c.get("combinedName"))
            self.combo_crop.addItem(clean_name, c["id"])

    def _autofill_probe_data(self):
        data = SensorService.read_sensor_data()
        if data.get("is_online", False):
            self.input_n.setText(str(data.get("nitrogen", 75.0)))
            self.input_p.setText(str(data.get("phosphorus", 40.0)))
            self.input_k.setText(str(data.get("potassium", 180.0)))
            self.input_ph.setText(str(data.get("ph", 6.8)))
            self.input_oc.setText("0.6")
        else:
            self.input_n.setText("75.0")
            self.input_p.setText("40.0")
            self.input_k.setText("180.0")
            self.input_ph.setText("6.8")
            self.input_oc.setText("0.5")

    def _run_calculation_and_show_results(self):
        try:
            n_val = float(self.input_n.text().strip() or "75.0")
            p_val = float(self.input_p.text().strip() or "40.0")
            k_val = float(self.input_k.text().strip() or "180.0")
            ph_val = float(self.input_ph.text().strip() or "6.8")
            oc_val = float(self.input_oc.text().strip() or "0.5")
        except ValueError:
            return

        state_idx = self.combo_state.currentIndex()
        district_idx = self.combo_district.currentIndex()
        crop_idx = self.combo_crop.currentIndex()

        state_id = self.states_list[state_idx]["id"] if state_idx >= 0 and self.states_list else "63f9322a89d86ca9e2bca5df"
        district_id = self.districts_list[district_idx]["id"] if district_idx >= 0 and self.districts_list else "63f949d189d86ca9e2bece50"
        crop_id = self.crops_list[crop_idx]["id"] if crop_idx >= 0 and self.crops_list else "6625fcb7c986db5da828c33d"
        crop_name = self.crops_list[crop_idx]["name"] if crop_idx >= 0 and self.crops_list else "Banana"

        is_natural = self.chk_natural.isChecked()

        result = FertilizerService.calculate_recommendation(
            state_id=state_id,
            district_id=district_id,
            crop_id=crop_id,
            crop_name=crop_name,
            n=n_val,
            p=p_val,
            k=k_val,
            oc=oc_val,
            ph=ph_val,
            natural_farming=is_natural
        )

        self.current_rec_result = result
        self._display_result(result)
        # Transition to View 1 (Prediction Dashboard)
        self.stack.setCurrentIndex(1)

    def _display_result(self, res: dict):
        if res.get("is_official_gov", False):
            self.source_pill.setText("● GOV PORTAL API")
            self.source_pill.setStyleSheet("background-color: #0b2e16; color: #22c55e; border: 1px solid #166534;")
        else:
            self.source_pill.setText("● AGRONOMIC ENGINE")
            self.source_pill.setStyleSheet("background-color: #0f1c30; color: #38bdf8; border: 1px solid #1e3a8a;")

        for i in reversed(range(self.output_layout.count())):
            item = self.output_layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        # Hero Crop Summary Banner Card
        crop_name = res.get("crop_name", "Crop").upper()
        hero_card = QFrame(self.output_container)
        hero_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #062a14, stop:1 #0f172a);
                border: 1px solid #166534;
                border-radius: 8px;
            }
        """)
        hl = QHBoxLayout(hero_card)
        hl.setContentsMargins(14, 10, 14, 10)

        h_ic = QLabel(hero_card)
        h_ic.setPixmap(qta.icon("fa5s.seedling", color="#22c55e").pixmap(28, 28))

        h_tb = QVBoxLayout()
        h_tb.setSpacing(2)
        h_t = QLabel(f"🌱 TARGET CROP: {crop_name}", hero_card)
        h_t.setStyleSheet(f"color: #ffffff; font-family: {FONT_FAMILY}; font-size: 12px; font-weight: 800;")
        h_sub = QLabel(res.get("summary_text", ""), hero_card)
        h_sub.setWordWrap(True)
        h_sub.setStyleSheet(f"color: #94a3b8; font-size: 10px;")

        h_tb.addWidget(h_t)
        h_tb.addWidget(h_sub)

        hl.addWidget(h_ic)
        hl.addLayout(h_tb, 1)

        self.output_layout.addWidget(hero_card)

        # Full-Width Categorized Dosage Cards Grid (3 Columns)
        dosages = res.get("dosages", {})
        grid_w = QWidget(self.output_container)
        grid_l = QGridLayout(grid_w)
        grid_l.setContentsMargins(0, 0, 0, 0)
        grid_l.setSpacing(8)

        colors = ["#22c55e", "#38bdf8", "#f59e0b", "#a855f7", "#06b6d4", "#ec4899"]
        grid_row = 0
        grid_col = 0

        for idx, (f_name, f_dose) in enumerate(dosages.items()):
            if isinstance(f_dose, dict):
                f_dose = f"{f_dose.get('value', '')} {f_dose.get('unit', '')}"

            f_str = str(f_dose)
            ic_name = _get_fertilizer_icon(str(f_name))

            card = QFrame(grid_w)
            card.setStyleSheet("""
                QFrame {
                    background-color: #0b101d;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(3)

            hdr_row = QHBoxLayout()
            c_ic = QLabel(card)
            c_ic.setPixmap(qta.icon(ic_name, color=colors[idx % len(colors)]).pixmap(14, 14))

            fn = QLabel(str(f_name), card)
            fn.setWordWrap(True)
            fn.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9.5px; font-weight: 700;")

            hdr_row.addWidget(c_ic)
            hdr_row.addWidget(fn, 1)

            c_color = colors[idx % len(colors)]
            fd = QLabel(f_str, card)
            fd.setWordWrap(True)
            fd.setStyleSheet(f"color: {c_color}; font-size: 12px; font-weight: 800; margin-top: 2px;")

            cl.addLayout(hdr_row)
            cl.addWidget(fd)

            # If long text (e.g. Bio-Fertilizers > 30 chars), span across all 3 columns
            if len(f_str) > 30 or "Bio-Fertilizer" in str(f_name):
                if grid_col > 0:
                    grid_row += 1
                    grid_col = 0
                grid_l.addWidget(card, grid_row, 0, 1, 3)
                grid_row += 1
                grid_col = 0
            else:
                grid_l.addWidget(card, grid_row, grid_col)
                grid_col += 1
                if grid_col > 2:
                    grid_col = 0
                    grid_row += 1

        self.output_layout.addWidget(grid_w)

        # Stage Application Timeline Schedule Cards
        schedule = res.get("schedule", [])
        if schedule:
            s_hdr = QLabel("📅 Application Stage Timeline Schedule:", self.output_container)
            s_hdr.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 800; margin-top: 6px;")
            self.output_layout.addWidget(s_hdr)

            for s_idx, item in enumerate(schedule):
                s_box = QFrame(self.output_container)
                s_box.setStyleSheet("""
                    QFrame {
                        background-color: #07140b;
                        border: 1px solid #14381e;
                        border-radius: 6px;
                    }
                """)
                sl = QVBoxLayout(s_box)
                sl.setContentsMargins(10, 8, 10, 8)
                sl.setSpacing(3)

                stg = QLabel(f"● {item['stage']}", s_box)
                stg.setWordWrap(True)
                stg.setStyleSheet("color: #22c55e; font-size: 10px; font-weight: 800;")

                dtl = QLabel(item["details"], s_box)
                dtl.setWordWrap(True)
                dtl.setStyleSheet(f"color: #ffffff; font-size: 9.5px; font-weight: 500;")

                sl.addWidget(stg)
                sl.addWidget(dtl)

                self.output_layout.addWidget(s_box)

    def _download_pdf_report(self):
        if not self.current_rec_result:
            return

        res = self.current_rec_result
        PDFExporter.export_single_session(
            session_type="Fertilizer Recommendation Schedule",
            session_data=res.get("dosages", {}),
            farmer_name="Kisan Farmer"
        )

        self.navigate_to_page.emit(6)
