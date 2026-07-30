"""
Report Page View for Project KISAN.
Timeline log of past sessions with PDF export engine triggers.
"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from database.models import CropRecommendationSession, FertilizerRecommendationSession, SoilTestSession
from utils.auth import AuthManager
from utils.pdf_exporter import PDFExporter
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
)


class ReportPage(QWidget):
    """Report Timeline Log & PDF Export View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        # Header Title + Export Full History Button
        hdr_layout = QHBoxLayout()

        title = QLabel("Farmer Analysis History & Reports", self)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_TITLE}; font-weight: 700;")

        self.btn_export_all = QPushButton("  Export Full History (PDF)", self)
        self.btn_export_all.setFixedHeight(34)
        self.btn_export_all.setCursor(Qt.PointingHandCursor)
        self.btn_export_all.setIcon(qta.icon("fa5s.file-pdf", color="#0a0f0a"))
        self.btn_export_all.setStyleSheet(f"background-color: {COLOR_PRIMARY_ACCENT}; color: #0a0f0a; border-radius: 5px; font-weight: 700; font-size: 11px; padding: 0 10px;")
        self.btn_export_all.clicked.connect(self._export_full_history)

        hdr_layout.addWidget(title)
        hdr_layout.addStretch(1)
        hdr_layout.addWidget(self.btn_export_all)

        layout.addLayout(hdr_layout)

        # Status Label
        self.status_lbl = QLabel("", self)
        self.status_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 600;")
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)

        # Scrollable Sessions Timeline List
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(8)

        scroll.setWidget(self.timeline_container)
        layout.addWidget(scroll, 1)

        # Load Timeline
        self.refresh_timeline()

    def refresh_timeline(self):
        for i in reversed(range(self.timeline_layout.count())):
            item = self.timeline_layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        farmer = AuthManager.get_current_farmer()
        farmer_id = farmer.id if farmer else 1
        farmer_name = farmer.full_name if farmer else "Farmer Profile"

        sessions = []

        # 1. Soil Tests
        soil_tests = SoilTestSession.query.filter_by(farmer_id=farmer_id).order_by(SoilTestSession.timestamp.desc()).all()
        for st in soil_tests:
            sessions.append({
                "type": "Soil Test Session",
                "timestamp": st.timestamp.strftime("%d %b %Y, %I:%M %p"),
                "summary": f"Sample {st.sample_id} • pH {st.ph}, N {st.nitrogen}, P {st.phosphorus}, K {st.potassium}",
                "icon": "fa5s.vial",
                "raw_data": {"sample_id": st.sample_id, "ph": st.ph, "nitrogen": st.nitrogen, "phosphorus": st.phosphorus, "potassium": st.potassium}
            })

        # 2. Crop Recommendations
        crop_recs = CropRecommendationSession.query.filter_by(farmer_id=farmer_id).order_by(CropRecommendationSession.timestamp.desc()).all()
        for cr in crop_recs:
            sessions.append({
                "type": "Crop Recommendation",
                "timestamp": cr.timestamp.strftime("%d %b %Y, %I:%M %p"),
                "summary": f"Land Size: {cr.land_size_acres} Acres ({cr.num_samples_taken} samples) • Model: {cr.model_version_used}",
                "icon": "fa5s.seedling",
                "raw_data": {"land_acres": cr.land_size_acres, "num_samples": cr.num_samples_taken, "avg_ph": cr.avg_ph, "avg_n": cr.avg_nitrogen}
            })

        # 3. Fertilizer Recommendations
        fert_recs = FertilizerRecommendationSession.query.filter_by(farmer_id=farmer_id).order_by(FertilizerRecommendationSession.timestamp.desc()).all()
        for fr in fert_recs:
            sessions.append({
                "type": "Fertilizer Recommendation",
                "timestamp": fr.timestamp.strftime("%d %b %Y, %I:%M %p"),
                "summary": f"Crop: {fr.crop} ({fr.district}, {fr.state}) • NPK: {fr.nitrogen}-{fr.phosphorus}-{fr.potassium}",
                "icon": "fa5s.prescription-bottle-alt",
                "raw_data": {"crop": fr.crop, "location": f"{fr.district}, {fr.state}", "input_npk": f"{fr.nitrogen}-{fr.phosphorus}-{fr.potassium}"}
            })

        self.loaded_sessions = sessions

        if not sessions:
            empty_lbl = QLabel("No test sessions recorded yet. Run a Soil Test or Recommendation first.", self.timeline_container)
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; padding: 20px;")
            self.timeline_layout.addWidget(empty_lbl)
            return

        for s in sessions:
            box = QFrame(self.timeline_container)
            box.setStyleSheet("background-color: #101910; border: 1px solid #1a291a; border-radius: 6px;")

            l = QHBoxLayout(box)
            l.setContentsMargins(10, 8, 10, 8)

            ic = QLabel(box)
            ic.setPixmap(qta.icon(s["icon"], color=COLOR_PRIMARY_ACCENT).pixmap(20, 20))

            info = QVBoxLayout()
            t = QLabel(f"{s['type']} • {s['timestamp']}", box)
            t.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 700;")
            sub = QLabel(s["summary"], box)
            sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")

            info.addWidget(t)
            info.addWidget(sub)

            btn_exp = QPushButton("PDF Export", box)
            btn_exp.setCursor(Qt.PointingHandCursor)
            btn_exp.setStyleSheet(f"background: #182818; color: {COLOR_PRIMARY_ACCENT}; border: 1px solid {COLOR_PRIMARY_ACCENT}; border-radius: 4px; font-size: 10px; font-weight: 600; padding: 4px 8px;")
            btn_exp.clicked.connect(lambda _, stype=s["type"], sdata=s["raw_data"]: self._export_single(stype, sdata))

            l.addWidget(ic)
            l.addLayout(info, 1)
            l.addWidget(btn_exp)

            self.timeline_layout.addWidget(box)

    def _export_single(self, stype: str, sdata: dict):
        farmer = AuthManager.get_current_farmer()
        fname = farmer.full_name if farmer else "Farmer Profile"
        path = PDFExporter.export_single_session(stype, sdata, fname)
        self.status_lbl.setText(f"✓ PDF Saved to Downloads: {path}")
        self.status_lbl.show()

    def _export_full_history(self):
        farmer = AuthManager.get_current_farmer()
        fname = farmer.full_name if farmer else "Farmer Profile"
        path = PDFExporter.export_full_history(getattr(self, "loaded_sessions", []), fname)
        self.status_lbl.setText(f"✓ Full History PDF Saved: {path}")
        self.status_lbl.show()
