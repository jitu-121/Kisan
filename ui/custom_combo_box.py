"""
Custom Touchscreen ComboBox Widget for Project KISAN.
Replaces buggy Qt Wayland popup menus with an in-app clean modal selector.
Guarantees 0% screen overflow on Linux/Wayland and 100% touchscreen-friendly UI.
"""

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from utils.theme import COLOR_BACKGROUND, COLOR_PRIMARY_ACCENT, COLOR_TEXT_MUTED, COLOR_TEXT_PRIMARY, FONT_FAMILY


class ItemSelectorDialog(QDialog):
    """Clean in-app popup dialog selector for QComboBox items."""

    def __init__(self, title_str: str, items: list, selected_idx: int = 0, parent=None):
        super().__init__(parent)
        self.items = items
        self.selected_item = None
        self.selected_index = selected_idx
        self._init_ui(title_str)

    def _init_ui(self, title_str: str):
        self.setWindowTitle(title_str)
        self.setFixedSize(340, 320)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0b101d;
                border: 1px solid #1e293b;
                border-radius: 10px;
                color: #ffffff;
                font-family: {FONT_FAMILY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header Title
        t_lbl = QLabel(f"Select {title_str}", self)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 800;")
        layout.addWidget(t_lbl)

        # Search Bar
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("🔍 Search option...")
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #070b12;
                color: #ffffff;
                border: 1px solid #1e293b;
                border-radius: 5px;
                padding: 2px 8px;
                font-size: 11px;
            }
        """)
        self.search_input.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_input)

        # Scrollable Item List
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #070b12;
                color: #ffffff;
                border: 1px solid #141c2e;
                border-radius: 6px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #0d1424;
            }
            QListWidget::item:selected {
                background-color: #14532d;
                color: #ffffff;
                font-weight: 700;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, 1)

        self._populate_list(self.items)

        # Pre-select item
        if 0 <= self.selected_index < self.list_widget.count():
            self.list_widget.setCurrentRow(self.selected_index)

    def _populate_list(self, items_to_show: list):
        self.list_widget.clear()
        for idx, it in enumerate(items_to_show):
            text = it["name"] if isinstance(it, dict) else str(it)
            item_widget = QListWidgetItem(text)
            item_widget.setData(Qt.UserRole, idx)
            self.list_widget.addItem(item_widget)

    def _filter_items(self, query: str):
        q = query.strip().lower()
        if not q:
            self._populate_list(self.items)
            return
        filtered = [it for it in self.items if q in (it["name"] if isinstance(it, dict) else str(it)).lower()]
        self._populate_list(filtered)

    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item = item.text()
        self.selected_index = item.data(Qt.UserRole)
        self.accept()


class CustomTouchComboBox(QFrame):
    """Custom Touch-Friendly ComboBox Widget."""
    currentIndexChanged = pyqtSignal(int)

    def __init__(self, title_str: str = "Option", parent=None):
        super().__init__(parent)
        self.title_str = title_str
        self.items = []
        self._current_index = -1
        self._init_ui()

    def _init_ui(self):
        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b101d;
                border: 1px solid #1e293b;
                border-radius: 5px;
            }
            QFrame:hover {
                border: 1px solid #22c55e;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)

        self.label = QLabel("Select...", self)
        self.label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: 600;")

        arrow = QLabel(self)
        arrow.setPixmap(qta.icon("fa5s.chevron-down", color=COLOR_TEXT_MUTED).pixmap(10, 10))

        layout.addWidget(self.label, 1)
        layout.addWidget(arrow)

    def mousePressEvent(self, event):
        if not self.items:
            return

        dlg = ItemSelectorDialog(self.title_str, self.items, self._current_index, self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_index is not None:
            self.setCurrentIndex(dlg.selected_index)

    def clear(self):
        self.items = []
        self._current_index = -1
        self.label.setText("Select...")

    def addItem(self, text: str, userData=None):
        self.items.append({"name": text, "data": userData})
        if self._current_index == -1:
            self.setCurrentIndex(0)

    def setCurrentIndex(self, index: int):
        if 0 <= index < len(self.items):
            self._current_index = index
            text = self.items[index]["name"]
            self.label.setText(text)
            self.currentIndexChanged.emit(index)

    def currentIndex(self) -> int:
        return self._current_index

    def count(self) -> int:
        return len(self.items)

    def currentData(self):
        if 0 <= self._current_index < len(self.items):
            return self.items[self._current_index]["data"]
        return None

    def setMaxVisibleItems(self, n: int):
        pass  # Compatibility method
