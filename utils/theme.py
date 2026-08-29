"""
Project KISAN - Theme & Styling Definitions
Centralized color palette, typography constants, and clean QSS stylesheet configurations.
Fixes QSS inheritance bugs and restricts QComboBox popup menus from expanding offscreen.
"""

# Color Palette Constants (Sleek Dark Navy / Emerald Design System)
COLOR_BACKGROUND = "#070b12"          # Deep dark navy-black canvas background
COLOR_SURFACE_NAVY = "#0d1424"        # Dark navy panel container surface
COLOR_SURFACE_GREEN = "#071c0f"       # Deep dark green panel container surface
COLOR_SURFACE_PURPLE = "#111428"      # Dark indigo/purple panel container surface
COLOR_PRIMARY_ACCENT = "#22c55e"     # Vibrant emerald green accent
COLOR_TEXT_PRIMARY = "#ffffff"       # Pure white text
COLOR_TEXT_MUTED = "#94a3b8"         # Cool gray muted text

# Sidebar Palette Constants
COLOR_SIDEBAR_BG = "#0b101d"          # Dark navy sidebar background
COLOR_SIDEBAR_HOVER = "#131b2e"       # Hover item state
COLOR_SIDEBAR_ACTIVE_BG = "#14532d"    # Active nav item background
COLOR_SIDEBAR_ACTIVE_ACCENT = "#22c55e"# Active green accent highlight
COLOR_BRANDING_BG = "#081c10"         # Bottom branding card background
COLOR_BRANDING_BORDER = "#164e26"     # Branding card green border

# Action Buttons Palette (Bottom Row)
COLOR_BTN_BLUE = "#1d4ed8"            # Re-Analyze Soil button
COLOR_BTN_TEAL = "#0e7490"            # Export Report button
COLOR_BTN_GOLD = "#854d0e"            # Calibrate Sensor button
COLOR_BTN_RED = "#991b1b"             # Shutdown System button

# Layout Dimensions
SIDEBAR_WIDTH = 205                   # Fixed width for touchscreen sidebar (out of 1024px)
NAV_ITEM_HEIGHT = 38                  # Touch target height per nav item
ICON_SIZE_NAV = 16                    # Compact icon size (in pixels)

# Typography & Font Family
FONT_FAMILY = '"Segoe UI", "Roboto", "Ubuntu", "Cantarell", sans-serif'

# Compact Font Size Constants (Tailored for 7-inch 1024x600 high-density screen)
FONT_SIZE_SMALL = "11px"
FONT_SIZE_NAV = "12px"
FONT_SIZE_BODY = "13px"
FONT_SIZE_HEADING = "15px"
FONT_SIZE_TITLE = "18px"

# Base Stylesheets (Scoped QSS to prevent QWidget child border inheritance)
MAIN_WINDOW_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_BACKGROUND};
    }}
    QWidget {{
        font-family: {FONT_FAMILY};
    }}
    QComboBox QAbstractItemView {{
        background-color: #0b101d;
        color: #ffffff;
        border: 1px solid #1e293b;
        selection-background-color: #166534;
        selection-color: #ffffff;
        outline: 0px;
    }}
    QComboBox QListView {{
        background-color: #0b101d;
        color: #ffffff;
        border: 1px solid #1e293b;
        outline: 0px;
    }}
    QComboBox QListView::item {{
        min-height: 24px;
        padding: 2px 6px;
        background-color: #0b101d;
        color: #ffffff;
    }}
    QComboBox QListView::item:selected {{
        background-color: #166534;
        color: #ffffff;
    }}
    QScrollBar:vertical {{
        border: none;
        background: #0b101d;
        width: 6px;
        margin: 0px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: #166534;
        min-height: 20px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #22c55e;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        border: none;
        background: none;
    }}
"""

SIDEBAR_STYLESHEET = f"""
    QWidget#SidebarWidget {{
        background-color: {COLOR_SIDEBAR_BG};
        border-right: 1px solid #141c2e;
    }}
    QWidget#SidebarWidget QLabel {{
        border: none;
        background: transparent;
    }}
"""

BRANDING_CARD_STYLESHEET = f"""
    QFrame#BrandingCard {{
        background-color: {COLOR_BRANDING_BG};
        border: 1px solid {COLOR_BRANDING_BORDER};
        border-radius: 8px;
    }}
    QFrame#BrandingCard QLabel {{
        border: none;
        background: transparent;
    }}
    QLabel#BrandingText {{
        color: {COLOR_PRIMARY_ACCENT};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_SMALL};
        font-weight: 700;
    }}
"""
