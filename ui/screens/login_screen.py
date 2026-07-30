"""
Login Screen implementation for Project KISAN.
Supports multi-farmer profile selection and credentials authentication.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta
from database.db import db_session
from database.models import Farmer
from utils.auth import AuthManager
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_BODY,
    FONT_SIZE_TITLE,
)


class LoginScreen(QWidget):
    """Farmer Login Screen View."""
    login_success = pyqtSignal(object)
    go_to_signup = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setAlignment(Qt.AlignCenter)

        # Login Box Container
        card = QFrame(self)
        card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #101a10;
                border: 1px solid #1a2a1a;
                border-radius: 10px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(10)

        # App Logo & Header
        icon_lbl = QLabel(card)
        icon_lbl.setAlignment(Qt.AlignCenter)
        pixmap = qta.icon("fa5s.seedling", color=COLOR_PRIMARY_ACCENT).pixmap(32, 32)
        icon_lbl.setPixmap(pixmap)

        title_lbl = QLabel("Project KISAN", card)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: {FONT_SIZE_TITLE}; font-weight: 700;")

        sub_lbl = QLabel("Farmer Profile Authentication", card)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-family: {FONT_FAMILY}; font-size: 11px;")

        # Inputs
        self.username_input = QLineEdit(card)
        self.username_input.setPlaceholderText("Enter Username")
        self.username_input.setFixedHeight(36)
        self.username_input.setStyleSheet(self._input_style())

        self.password_input = QLineEdit(card)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(36)
        self.password_input.setStyleSheet(self._input_style())

        # Error Label
        self.error_label = QLabel("", card)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #ff4d4d; font-size: 11px; font-weight: 600;")
        self.error_label.hide()

        # Login Button
        self.login_btn = QPushButton("Log In", card)
        self.login_btn.setFixedHeight(38)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_ACCENT};
                color: #0a0f0a;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #00b368;
            }}
        """)
        self.login_btn.clicked.connect(self._handle_login)

        # Signup Redirect
        signup_layout = QHBoxLayout()
        signup_layout.setAlignment(Qt.AlignCenter)

        signup_text = QLabel("New Farmer?", card)
        signup_text.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        signup_btn = QPushButton("Create Account", card)
        signup_btn.setCursor(Qt.PointingHandCursor)
        signup_btn.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        signup_btn.clicked.connect(self.go_to_signup.emit)

        signup_layout.addWidget(signup_text)
        signup_layout.addWidget(signup_btn)

        # Assemble
        card_layout.addWidget(icon_lbl)
        card_layout.addWidget(title_lbl)
        card_layout.addWidget(sub_lbl)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.login_btn)
        card_layout.addLayout(signup_layout)

        layout.addWidget(card)

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: #0a0f0a;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid #1a2a1a;
                border-radius: 6px;
                padding: 0 10px;
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_PRIMARY_ACCENT};
            }}
        """

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        farmer = db_session.query(Farmer).filter_by(username=username).first()
        if not farmer:
            self._show_error("Farmer profile not found.")
            return

        if not AuthManager.verify_password(password, farmer.password_hash):
            self._show_error("Invalid password.")
            return

        self.error_label.hide()
        AuthManager.set_current_farmer(farmer)
        self.login_success.emit(farmer)

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()
