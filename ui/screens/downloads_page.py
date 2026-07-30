"""
Downloads Page View for Project KISAN.
Includes an In-App PDF Document Reader using QStackedWidget and pdftoppm.
Guarantees 100% in-app rendering within the 7-inch display boundaries.
"""

import glob, os, shutil, subprocess, tempfile
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from utils.pdf_exporter import get_downloads_dir
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
)


class DownloadsPage(QWidget):
    """In-App PDF Downloads Manager & Embedded Reader View."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_preview_dir = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget(self)
        main_layout.addWidget(self.stack)

        # ---------------------------------------------------------------------
        # VIEW 0: PDF Downloads History List
        # ---------------------------------------------------------------------
        self.view_list = QWidget()
        v_list_layout = QVBoxLayout(self.view_list)
        v_list_layout.setContentsMargins(16, 10, 16, 10)
        v_list_layout.setSpacing(8)

        # Header Bar
        hdr_layout = QHBoxLayout()

        title = QLabel("Exported Reports & Downloads History", self.view_list)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_TITLE}; font-weight: 700;")

        btn_del_all = QPushButton("🗑 Clear All Reports", self.view_list)
        btn_del_all.setCursor(Qt.PointingHandCursor)
        btn_del_all.setStyleSheet("""
            QPushButton {
                background: #450a0a;
                color: #f87171;
                border: 1px solid #991b1b;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10.5px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: #991b1b;
                color: #ffffff;
            }
        """)
        btn_del_all.clicked.connect(self._clear_all_pdfs)

        btn_ref = QPushButton("🔄 Refresh List", self.view_list)
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.setStyleSheet("""
            QPushButton {
                background: #182818;
                color: #00d97e;
                border: 1px solid #00d97e;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10.5px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: #166534;
            }
        """)
        btn_ref.clicked.connect(self.refresh_list)

        hdr_layout.addWidget(title)
        hdr_layout.addStretch(1)
        hdr_layout.addWidget(btn_del_all)
        hdr_layout.addWidget(btn_ref)

        v_list_layout.addLayout(hdr_layout)

        # Scrollable PDF files list (No horizontal scrollbar!)
        scroll = QScrollArea(self.view_list)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        scroll.setWidget(self.list_container)
        v_list_layout.addWidget(scroll, 1)

        self.stack.addWidget(self.view_list)

        # ---------------------------------------------------------------------
        # VIEW 1: In-App Embedded PDF Document Viewer
        # ---------------------------------------------------------------------
        self.view_reader = QWidget()
        v_reader_layout = QVBoxLayout(self.view_reader)
        v_reader_layout.setContentsMargins(12, 8, 12, 8)
        v_reader_layout.setSpacing(8)

        # Reader Header Bar
        reader_hdr = QHBoxLayout()

        btn_back = QPushButton("⬅ Back to Downloads", self.view_reader)
        btn_back.setFixedHeight(30)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 5px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        btn_back.clicked.connect(self._close_pdf_reader)

        self.reader_title = QLabel("PDF Reader", self.view_reader)
        self.reader_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11.5px; font-weight: 800;")

        self.btn_delete_current = QPushButton("🗑 Delete", self.view_reader)
        self.btn_delete_current.setFixedHeight(30)
        self.btn_delete_current.setCursor(Qt.PointingHandCursor)
        self.btn_delete_current.setStyleSheet("""
            QPushButton {
                background-color: #7f1d1d;
                color: #ffffff;
                border: 1px solid #ef4444;
                border-radius: 5px;
                font-size: 10.5px;
                font-weight: 700;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)

        reader_hdr.addWidget(btn_back)
        reader_hdr.addWidget(self.reader_title, 1)
        reader_hdr.addWidget(self.btn_delete_current)

        v_reader_layout.addLayout(reader_hdr)

        div_reader = QFrame(self.view_reader)
        div_reader.setFixedHeight(1)
        div_reader.setStyleSheet("background-color: #1e293b;")
        v_reader_layout.addWidget(div_reader)

        # Scrollable Image Pages Container
        reader_scroll = QScrollArea(self.view_reader)
        reader_scroll.setWidgetResizable(True)
        reader_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        reader_scroll.setStyleSheet("QScrollArea { border: none; background: #070b12; border-radius: 8px; }")

        self.reader_pages_container = QWidget()
        self.reader_pages_layout = QVBoxLayout(self.reader_pages_container)
        self.reader_pages_layout.setContentsMargins(10, 10, 10, 10)
        self.reader_pages_layout.setSpacing(12)
        self.reader_pages_layout.setAlignment(Qt.AlignHCenter)

        reader_scroll.setWidget(self.reader_pages_container)
        v_reader_layout.addWidget(reader_scroll, 1)

        self.stack.addWidget(self.view_reader)

        # Load initial list
        self.refresh_list()

    def refresh_list(self):
        for i in reversed(range(self.list_layout.count())):
            item = self.list_layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        downloads_dir = get_downloads_dir()
        pdf_pattern = os.path.join(downloads_dir, "KISAN_*.pdf")
        pdf_files = sorted(glob.glob(pdf_pattern), key=os.path.getmtime, reverse=True)

        if not pdf_files:
            empty_box = QFrame(self.list_container)
            empty_box.setStyleSheet("background-color: #0b101d; border: 1px dashed #1e293b; border-radius: 8px;")
            eb_l = QVBoxLayout(empty_box)
            eb_l.setContentsMargins(20, 30, 20, 30)
            eb_l.setAlignment(Qt.AlignCenter)

            ic = QLabel(empty_box)
            ic.setPixmap(qta.icon("fa5s.folder-open", color="#334155").pixmap(36, 36))
            ic.setAlignment(Qt.AlignCenter)

            t = QLabel("No PDF Reports Found", empty_box)
            t.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 700; margin-top: 6px;")
            t.setAlignment(Qt.AlignCenter)

            sub = QLabel("Export a Soil Test or Fertilizer Recommendation report to view it here in-app.", empty_box)
            sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; text-align: center; margin-top: 4px;")
            sub.setAlignment(Qt.AlignCenter)

            eb_l.addWidget(ic)
            eb_l.addWidget(t)
            eb_l.addWidget(sub)

            self.list_layout.addWidget(empty_box)
            return

        for filepath in pdf_files:
            filename = os.path.basename(filepath)
            size_kb = round(os.path.getsize(filepath) / 1024, 1)

            box = QFrame(self.list_container)
            box.setCursor(Qt.PointingHandCursor)
            box.setStyleSheet("""
                QFrame {
                    background-color: #0b101d;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }
                QFrame:hover {
                    border: 1px solid #22c55e;
                }
            """)

            l = QHBoxLayout(box)
            l.setContentsMargins(12, 8, 12, 8)
            l.setSpacing(10)

            ic = QLabel(box)
            ic.setPixmap(qta.icon("fa5s.file-pdf", color=COLOR_PRIMARY_ACCENT).pixmap(24, 24))

            info = QVBoxLayout()
            info.setSpacing(2)
            t = QLabel(filename, box)
            t.setWordWrap(True)
            t.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 700;")
            sub = QLabel(f"Location: {filepath} • Size: {size_kb} KB", box)
            sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9.5px;")

            info.addWidget(t)
            info.addWidget(sub)

            # Action Buttons
            b_box = QHBoxLayout()
            b_box.setSpacing(6)

            btn_view = QPushButton("👁 View PDF", box)
            btn_view.setFixedHeight(28)
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet("""
                QPushButton {
                    background-color: #14532d;
                    color: #ffffff;
                    border: 1px solid #22c55e;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 700;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #166534;
                }
            """)
            btn_view.clicked.connect(lambda _, fp=filepath: self._open_pdf_in_app(fp))

            btn_del = QPushButton("🗑", box)
            btn_del.setFixedSize(28, 28)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #450a0a;
                    color: #f87171;
                    border: 1px solid #991b1b;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #991b1b;
                    color: #ffffff;
                }
            """)
            btn_del.clicked.connect(lambda _, fp=filepath: self._delete_pdf_file(fp))

            b_box.addWidget(btn_view)
            b_box.addWidget(btn_del)

            l.addWidget(ic)
            l.addLayout(info, 1)
            l.addLayout(b_box)

            # Make entire box clickable to open in-app PDF reader
            box.mousePressEvent = lambda ev, fp=filepath: self._open_pdf_in_app(fp)

            self.list_layout.addWidget(box)

    def _open_pdf_in_app(self, filepath: str):
        """Render PDF pages to images using pdftoppm and display in-app."""
        if not os.path.exists(filepath):
            return

        filename = os.path.basename(filepath)
        self.reader_title.setText(f"📄 {filename}")
        try:
            self.btn_delete_current.clicked.disconnect()
        except Exception:
            pass
        self.btn_delete_current.clicked.connect(lambda: self._delete_and_close(filepath))

        # Clear previous rendered page labels
        for i in reversed(range(self.reader_pages_layout.count())):
            item = self.reader_pages_layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        # Cleanup old tmp preview dir
        if self.current_preview_dir and os.path.exists(self.current_preview_dir):
            shutil.rmtree(self.current_preview_dir, ignore_errors=True)

        self.current_preview_dir = tempfile.mkdtemp(prefix="kisan_pdf_")

        # Convert PDF pages to crisp PNGs using pdftoppm
        cmd = ["pdftoppm", "-png", "-r", "150", filepath, os.path.join(self.current_preview_dir, "page")]
        try:
            subprocess.run(cmd, check=True)
            page_pngs = sorted(glob.glob(os.path.join(self.current_preview_dir, "page-*.png")))

            for page_path in page_pngs:
                lbl = QLabel(self.reader_pages_container)
                pixmap = QPixmap(page_path)
                # Scale to fit touchscreen width cleanly (~650px)
                scaled = pixmap.scaledToWidth(650, Qt.SmoothTransformation)
                lbl.setPixmap(scaled)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("border: 1px solid #1e293b; border-radius: 4px; background-color: #ffffff;")

                self.reader_pages_layout.addWidget(lbl)
        except Exception as e:
            err_lbl = QLabel(f"Failed to render PDF: {e}", self.reader_pages_container)
            err_lbl.setStyleSheet("color: #ef4444; font-size: 11px;")
            self.reader_pages_layout.addWidget(err_lbl)

        # Switch to View 1 (In-App Reader)
        self.stack.setCurrentIndex(1)

    def _close_pdf_reader(self):
        """Switch back to View 0 (Downloads List)."""
        self.stack.setCurrentIndex(0)

    def _delete_pdf_file(self, filepath: str):
        """Delete single PDF file and refresh list."""
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[Delete PDF Error] {e}")
        self.refresh_list()

    def _delete_and_close(self, filepath: str):
        """Delete PDF file and return to list."""
        self._delete_pdf_file(filepath)
        self._close_pdf_reader()

    def _clear_all_pdfs(self):
        """Delete all PDF files in downloads folder."""
        downloads_dir = get_downloads_dir()
        pdf_files = glob.glob(os.path.join(downloads_dir, "KISAN_*.pdf"))
        for fp in pdf_files:
            try:
                os.remove(fp)
            except Exception as e:
                print(f"[Clear All PDF Error] {e}")
        self.refresh_list()
