"""
Signup Screen implementation for Project KISAN.
Allows self-registration for farmers on shared device.
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
    FONT_SIZE_TITLE,
)


class SignupScreen(QWidget):
    """Farmer Self-Registration View."""
    signup_success = pyqtSignal()
    go_to_login = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 10, 40, 10)
        layout.setAlignment(Qt.AlignCenter)

        # Signup Card Container
        card = QFrame(self)
        card.setFixedWidth(440)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #101a10;
                border: 1px solid #1a2a1a;
                border-radius: 10px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 16, 24, 16)
        card_layout.setSpacing(8)

        # Title Header
        title_lbl = QLabel("Create Farmer Account", card)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-family: {FONT_FAMILY}; font-size: {FONT_SIZE_TITLE}; font-weight: 700;")

        # Inputs
        self.fullname_input = QLineEdit(card)
        self.fullname_input.setPlaceholderText("Full Name *")
        self.fullname_input.setFixedHeight(32)
        self.fullname_input.setStyleSheet(self._input_style())

        self.username_input = QLineEdit(card)
        self.username_input.setPlaceholderText("Username (unique) *")
        self.username_input.setFixedHeight(32)
        self.username_input.setStyleSheet(self._input_style())

        self.password_input = QLineEdit(card)
        self.password_input.setPlaceholderText("Password *")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(32)
        self.password_input.setStyleSheet(self._input_style())

        self.confirm_password_input = QLineEdit(card)
        self.confirm_password_input.setPlaceholderText("Confirm Password *")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFixedHeight(32)
        self.confirm_password_input.setStyleSheet(self._input_style())

        self.phone_input = QLineEdit(card)
        self.phone_input.setPlaceholderText("Phone Number (Optional)")
        self.phone_input.setFixedHeight(32)
        self.phone_input.setStyleSheet(self._input_style())

        self.location_input = QLineEdit(card)
        self.location_input.setPlaceholderText("Village / Location (Optional)")
        self.location_input.setFixedHeight(32)
        self.location_input.setStyleSheet(self._input_style())

        # Error Label
        self.error_label = QLabel("", card)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #ff4d4d; font-size: 11px; font-weight: 600;")
        self.error_label.hide()

        # Submit Button
        self.submit_btn = QPushButton("Register Farmer Profile", card)
        self.submit_btn.setFixedHeight(36)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY_ACCENT};
                color: #0a0f0a;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #00b368;
            }}
        """)
        self.submit_btn.clicked.connect(self._handle_signup)

        # Back to login
        back_layout = QHBoxLayout()
        back_layout.setAlignment(Qt.AlignCenter)

        back_text = QLabel("Already registered?", card)
        back_text.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        back_btn = QPushButton("Log In", card)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"color: {COLOR_PRIMARY_ACCENT}; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        back_btn.clicked.connect(self.go_to_login.emit)

        back_layout.addWidget(back_text)
        back_layout.addWidget(back_btn)

        # Assemble
        card_layout.addWidget(title_lbl)
        card_layout.addWidget(self.fullname_input)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addWidget(self.phone_input)
        card_layout.addWidget(self.location_input)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.submit_btn)
        card_layout.addLayout(back_layout)

        layout.addWidget(card)

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: #0a0f0a;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid #1a2a1a;
                border-radius: 5px;
                padding: 0 8px;
                font-family: {FONT_FAMILY};
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_PRIMARY_ACCENT};
            }}
        """

    def _handle_signup(self):
        fullname = self.fullname_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_pass = self.confirm_password_input.text().strip()
        phone = self.phone_input.text().strip()
        location = self.location_input.text().strip()

        if not fullname or not username or not password:
            self._show_error("Full Name, Username, and Password are required.")
            return

        if password != confirm_pass:
            self._show_error("Passwords do not match.")
            return

        existing = db_session.query(Farmer).filter_by(username=username).first()
        if existing:
            self._show_error("Username is already taken. Choose another.")
            return

        # Create Farmer Profile
        hashed = AuthManager.hash_password(password)
        new_farmer = Farmer(
            full_name=fullname,
            username=username,
            password_hash=hashed,
            phone_number=phone,
            village_or_location=location
        )
        db_session.add(new_farmer)
        db_session.commit()

        self.error_label.hide()
        self.signup_success.emit()

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()
