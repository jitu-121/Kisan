"""
On-Screen Touch Keyboard Component for Project KISAN.
Reusable touch keyboard overlay sliding up when text inputs are focused.
"""

from PyQt5.QtCore import QEvent, QObject, QPropertyAnimation, QRect, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_SIDEBAR_BG,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class TouchKeyButton(QPushButton):
    """Touch-optimized keypad button."""

    def __init__(self, text: str, parent=None, is_special=False):
        super().__init__(text, parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedHeight(34)
        bg = "#1f2d1f" if is_special else "#151f15"
        color = COLOR_PRIMARY_ACCENT if is_special else COLOR_TEXT_PRIMARY

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: 1px solid #283a28;
                border-radius: 4px;
                font-family: {FONT_FAMILY};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_PRIMARY_ACCENT};
                color: #0a0f0a;
            }}
        """)


class TouchKeyboardWidget(QFrame):
    """
    On-Screen Touch Keyboard Panel.
    Captures target input widget and types characters directly.
    """
    hidden_signal = pyqtSignal()

    KEY_ROWS = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "⌫"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
        ["Shift", "z", "x", "c", "v", "b", "n", "m", "Clear"],
        ["Space", "Close Keyboard"]
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_input = None
        self.is_shift = False
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #0d140d;
                border-top: 2px solid {COLOR_PRIMARY_ACCENT};
                border-radius: 8px 8px 0 0;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        for row in self.KEY_ROWS:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(3)

            for key in row:
                is_special = key in ["⌫", "Shift", "Clear", "Close Keyboard", "Space"]
                btn = TouchKeyButton(key, self, is_special=is_special)
                btn.clicked.connect(lambda _, k=key: self._handle_key_press(k))

                if key == "Space":
                    row_layout.addWidget(btn, 4)
                elif key == "Close Keyboard":
                    row_layout.addWidget(btn, 2)
                else:
                    row_layout.addWidget(btn, 1)

            layout.addLayout(row_layout)

        self.hide()

    def attach_to_input(self, input_widget):
        """Bind keyboard to a QLineEdit or QTextEdit target."""
        self.target_input = input_widget
        self.show()

    def _handle_key_press(self, key: str):
        if not self.target_input:
            return

        if key == "Close Keyboard":
            self.hide()
            self.hidden_signal.emit()
            return
        elif key == "⌫":
            if isinstance(self.target_input, QLineEdit):
                self.target_input.backspace()
            elif isinstance(self.target_input, QTextEdit):
                cursor = self.target_input.textCursor()
                cursor.deletePreviousChar()
        elif key == "Clear":
            self.target_input.clear()
        elif key == "Space":
            self._insert_char(" ")
        elif key == "Shift":
            self.is_shift = not self.is_shift
        else:
            char = key.upper() if self.is_shift else key.lower()
            self._insert_char(char)
            if self.is_shift:
                self.is_shift = False

    def _insert_char(self, char: str):
        if isinstance(self.target_input, QLineEdit):
            self.target_input.insert(char)
        elif isinstance(self.target_input, QTextEdit):
            self.target_input.insertPlainText(char)


class TouchKeyboardFocusFilter(QObject):
    """
    Global Event Filter listening for FocusIn events on QLineEdit inputs
    to automatically pop up the touch keyboard.
    """

    def __init__(self, keyboard_widget: TouchKeyboardWidget, parent=None):
        super().__init__(parent)
        self.keyboard = keyboard_widget

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, (QLineEdit, QTextEdit)):
                self.keyboard.attach_to_input(obj)
        return super().eventFilter(obj, event)
