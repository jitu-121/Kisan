"""
Reusable Placeholder Page Widget for Project KISAN.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_HEADING,
)


class PlaceholderPage(QWidget):
    """
    Simple placeholder page widget displaying page title + '— Coming Soon'.
    """

    def __init__(self, page_name: str, parent=None):
        super().__init__(parent)
        self.page_name = page_name
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        display_text = (
            "Project KISAN — Base Window"
            if self.page_name == "Dashboard"
            else f"{self.page_name} — Coming Soon"
        )

        self.label = QLabel(display_text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"font-family: {FONT_FAMILY}; "
            f"font-size: {FONT_SIZE_HEADING}; "
            f"font-weight: 500;"
        )

        layout.addWidget(self.label)
