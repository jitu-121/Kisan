"""
Entry point for Project KISAN desktop application.
Initializes database, global touch keyboard filter, and launches main window.
"""

import sys
from PyQt5.QtWidgets import QApplication
from database import init_db
from ui.main_window import MainWindow
from ui.touch_keyboard import TouchKeyboardFocusFilter


def main():
    init_db()
    app = QApplication(sys.argv)

    window = MainWindow()

    # Register global Touch Keyboard event filter
    kb_filter = TouchKeyboardFocusFilter(window.touch_keyboard, window)
    app.installEventFilter(kb_filter)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
