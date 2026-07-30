"""
Sidebar Navigation Widget for Project KISAN.
Scoped QSS styling to eliminate wireframe box outlines on child widgets.
"""

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from utils.theme import (
    BRANDING_CARD_STYLESHEET,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_NAV,
    ICON_SIZE_NAV,
    NAV_ITEM_HEIGHT,
    SIDEBAR_STYLESHEET,
    SIDEBAR_WIDTH,
)


class NavItemWidget(QFrame):
    """Individual navigation bar item with clean QSS styles."""
    clicked = pyqtSignal(int)

    def __init__(self, index: int, text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("NavItemWidget")
        self.index = index
        self.text = text
        self.icon_name = icon_name
        self.is_active = False
        self.is_hovered = False
        self._init_ui()

    def _init_ui(self):
        self.setFixedHeight(NAV_ITEM_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(8)

        # Icon Label
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(ICON_SIZE_NAV, ICON_SIZE_NAV)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # Text Label
        self.text_label = QLabel(self.text, self)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label, 1)

        self._update_appearance()

    def set_active(self, active: bool):
        self.is_active = active
        self._update_appearance()

    def _update_appearance(self):
        if self.is_active:
            style = f"""
                QFrame#NavItemWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14532d, stop:1 #166534);
                    border: 1px solid {COLOR_PRIMARY_ACCENT};
                    border-radius: 8px;
                }}
                QFrame#NavItemWidget QLabel {{
                    border: none;
                    background: transparent;
                }}
            """
            text_color = COLOR_TEXT_PRIMARY
            icon_color = COLOR_PRIMARY_ACCENT
            font_weight = "700"
        elif self.is_hovered:
            style = """
                QFrame#NavItemWidget {
                    background-color: #131b2e;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame#NavItemWidget QLabel {
                    border: none;
                    background: transparent;
                }
            """
            text_color = COLOR_TEXT_PRIMARY
            icon_color = COLOR_TEXT_PRIMARY
            font_weight = "500"
        else:
            style = """
                QFrame#NavItemWidget {
                    background-color: transparent;
                    border: none;
                }
                QFrame#NavItemWidget QLabel {
                    border: none;
                    background: transparent;
                }
            """
            text_color = COLOR_TEXT_MUTED
            icon_color = COLOR_TEXT_MUTED
            font_weight = "500"

        self.setStyleSheet(style)

        pixmap = qta.icon(self.icon_name, color=icon_color).pixmap(
            QSize(ICON_SIZE_NAV, ICON_SIZE_NAV)
        )
        self.icon_label.setPixmap(pixmap)

        self.text_label.setStyleSheet(
            f"color: {text_color}; "
            f"font-family: {FONT_FAMILY}; "
            f"font-size: {FONT_SIZE_NAV}; "
            f"font-weight: {font_weight}; "
            f"border: none; background: transparent;"
        )

    def enterEvent(self, event):
        self.is_hovered = True
        self._update_appearance()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self._update_appearance()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)


class BrandingCard(QFrame):
    """Bottom branding card for Project KISAN."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BrandingCard")
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(BRANDING_CARD_STYLESHEET)
        self.setFixedHeight(76)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Plant / Growth Icon
        icon_label = QLabel(self)
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        pixmap = qta.icon("fa5s.seedling", color=COLOR_PRIMARY_ACCENT).pixmap(
            QSize(24, 24)
        )
        icon_label.setPixmap(pixmap)

        # Slogan Text
        text_label = QLabel("Healthy Soil\nBetter Tomorrow", self)
        text_label.setObjectName("BrandingText")
        text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon_label, 0, Qt.AlignCenter)
        layout.addWidget(text_label, 0, Qt.AlignCenter)


class SidebarWidget(QWidget):
    """Sidebar navigation widget container."""
    item_selected = pyqtSignal(int)

    NAV_ITEMS = [
        ("Dashboard", "fa5s.th-large"),
        ("Soil Test", "fa5s.vial"),
        ("Crop Recommendation", "fa5s.seedling"),
        ("Fertilizer Recommendation", "fa5s.prescription-bottle-alt"),
        ("Weather Report", "fa5s.cloud-sun"),
        ("Report", "fa5s.file-alt"),
        ("Downloads", "fa5s.download"),
        ("Settings", "fa5s.cog"),
        ("About System", "fa5s.info-circle"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.nav_buttons = []
        self.current_active_index = 0
        self._init_ui()

    def _init_ui(self):
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(SIDEBAR_STYLESHEET)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 8, 6, 8)
        main_layout.setSpacing(2)

        # Create Navigation Items
        for idx, (name, icon_name) in enumerate(self.NAV_ITEMS):
            nav_item = NavItemWidget(idx, name, icon_name, self)
            nav_item.clicked.connect(self._on_item_clicked)
            main_layout.addWidget(nav_item)
            self.nav_buttons.append(nav_item)

        # Spacer to push branding card to bottom
        main_layout.addStretch(1)

        # Bottom Branding Card
        self.branding_card = BrandingCard(self)
        main_layout.addWidget(self.branding_card)

        # Set default active item (Dashboard)
        self.set_active_index(0)

    def _on_item_clicked(self, index: int):
        if index != self.current_active_index:
            self.set_active_index(index)
            self.item_selected.emit(index)

    def set_active_index(self, index: int):
        self.current_active_index = index
        for btn in self.nav_buttons:
            btn.set_active(btn.index == index)
