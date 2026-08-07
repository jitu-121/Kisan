"""
Main Window view implementation for Project KISAN.
Bypasses Login/Signup for direct boot flow:
SplashScreen (3-sec logo reveal) -> Dashboard & Main Application Shell.
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget
from database import init_db
from ui.animated_stacked_widget import AnimatedStackedWidget
from ui.screens.about_page import AboutPage
from ui.screens.crop_rec_page import CropRecPage
from ui.screens.dashboard_page import DashboardPage
from ui.screens.downloads_page import DownloadsPage
from ui.screens.fertilizer_rec_page import FertilizerRecPage
from ui.screens.report_page import ReportPage
from ui.screens.settings_page import SettingsPage
from ui.screens.soil_test_page import SoilTestPage
from ui.screens.weather_page import WeatherPage
from ui.sidebar import SidebarWidget
from ui.splash_screen import SplashScreen
from ui.top_bar import TopBarWidget
from ui.touch_keyboard import TouchKeyboardFocusFilter, TouchKeyboardWidget
from utils.theme import MAIN_WINDOW_STYLESHEET


class MainWindow(QMainWindow):
    """
    Main Application Window for Project KISAN.
    Fixed resolution: 1024x600 (Waveshare 7-inch IPS touchscreen target).
    Direct boot flow: Splash Screen (3 sec) -> Dashboard (Main App Shell).
    """

    def __init__(self):
        super().__init__()
        init_db()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Project KISAN")
        self.setFixedSize(1024, 600)
        self.setStyleSheet(MAIN_WINDOW_STYLESHEET)

        # Central Root Container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Bar (40px)
        self.top_bar = TopBarWidget(self)
        root_layout.addWidget(self.top_bar)

        # 2. Main Body (Sidebar + Content Stack)
        body_widget = QWidget(self)
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Sidebar (215px)
        self.sidebar = SidebarWidget(self)
        body_layout.addWidget(self.sidebar)

        # Right Main Content Stack (Animated)
        self.content_stack = AnimatedStackedWidget(self)
        body_layout.addWidget(self.content_stack, 1)

        root_layout.addWidget(body_widget, 1)

        # 3. Touch Keyboard Overlay Widget
        self.touch_keyboard = TouchKeyboardWidget(self)

        # --- Stack Indices Definition ---
        # Index 0: Splash Screen (3-second startup animation)
        self.splash_screen = SplashScreen(self, duration_ms=3000)
        self.splash_screen.animation_finished.connect(self._on_splash_finished)
        self.content_stack.addWidget(self.splash_screen)

        # Indices 1 to 9: Content Pages matching Sidebar items 0 to 8
        self.dashboard_page = DashboardPage(self)
        self.dashboard_page.navigate_to_page.connect(self._on_sidebar_item_selected)
        self.dashboard_page.shutdown_trigger.connect(self.close)
        self.content_stack.addWidget(self.dashboard_page)

        self.soil_test_page = SoilTestPage(self)
        self.soil_test_page.navigate_to_page.connect(self._on_sidebar_item_selected)
        self.content_stack.addWidget(self.soil_test_page)

        self.crop_rec_page = CropRecPage(self)
        self.crop_rec_page.navigate_to_page.connect(self._on_sidebar_item_selected)
        self.content_stack.addWidget(self.crop_rec_page)

        self.fertilizer_rec_page = FertilizerRecPage(self)
        self.fertilizer_rec_page.navigate_to_page.connect(self._on_sidebar_item_selected)
        self.content_stack.addWidget(self.fertilizer_rec_page)


        self.weather_page = WeatherPage(self)
        self.content_stack.addWidget(self.weather_page)

        self.report_page = ReportPage(self)
        self.content_stack.addWidget(self.report_page)

        self.downloads_page = DownloadsPage(self)
        self.content_stack.addWidget(self.downloads_page)

        self.settings_page = SettingsPage(self)
        self.content_stack.addWidget(self.settings_page)

        self.about_page = AboutPage(self)
        self.content_stack.addWidget(self.about_page)

        # Connect Sidebar Selection Signal
        self.sidebar.item_selected.connect(self._on_sidebar_item_selected)

        # --- Initial Startup Mode: Show Splash Screen & Hide TopBar/Sidebar ---
        self.top_bar.hide()
        self.sidebar.hide()
        self.content_stack.setCurrentIndex(0)

        # Trigger 3-second splash animation start after window opens
        QTimer.singleShot(100, self.splash_screen.start_splash_animation)

    def _on_splash_finished(self):
        """Called automatically after 3-second splash screen animation finishes."""
        self.top_bar.show()
        self.sidebar.show()
        self.sidebar.set_active_index(0)
        self.content_stack.set_current_index_animated(1)  # Transition directly to Dashboard

    def _on_sidebar_item_selected(self, sidebar_idx: int):
        self.sidebar.set_active_index(sidebar_idx)
        stack_idx = sidebar_idx + 1
        self.content_stack.set_current_index_animated(stack_idx)

        # Refresh page data on navigation
        if sidebar_idx == 5:  # Report page
            self.report_page.refresh_timeline()
        elif sidebar_idx == 6:  # Downloads page
            self.downloads_page.refresh_list()
