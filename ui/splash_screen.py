"""
Splash Screen implementation for Project KISAN.
Features a single aesthetic falling logo leaf animation with gentle sway physics,
soft aura pulse landing, and smooth title reveal.
"""

import math
from PyQt5.QtCore import QEasingCurve, QParallelAnimationGroup, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QFrame, QGraphicsOpacityEffect, QLabel, QProgressBar, QVBoxLayout, QWidget
import qtawesome as qta
from utils.theme import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


def draw_leaf_shape(painter: QPainter, size: float, color: QColor):
    """Draw a beautifully detailed natural leaf shape with central vein."""
    path = QPainterPath()
    path.moveTo(0, -size / 2.0)
    path.cubicTo(size / 1.8, -size / 4.0, size / 1.8, size / 4.0, 0, size / 2.0)
    path.cubicTo(-size / 1.8, size / 4.0, -size / 1.8, -size / 4.0, 0, -size / 2.0)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color))
    painter.drawPath(path)

    # Central Vein line
    pen = QPen(QColor(255, 255, 255, 140), 1.2)
    painter.setPen(pen)
    painter.drawLine(QPointF(0, -size / 2.2), QPointF(0, size / 1.8))


class SingleLeafCanvasWidget(QWidget):
    """60 FPS Custom Canvas for the single aesthetic falling & swaying main logo leaf."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)

        self.canvas_w = 1024
        self.canvas_h = 600

        # Hero Leaf Physics Parameters
        self.target_y = 190.0
        self.size = 46.0
        self.reset()

    def reset(self):
        self.x_center = self.canvas_w / 2.0
        self.leaf_y = -60.0
        self.leaf_x = self.x_center
        self.vy = 2.4
        self.sway_amplitude = 45.0
        self.sway_freq = 0.035
        self.sway_phase = 0.0

        self.rotation = -25.0
        self.rotation_speed = 0.8
        self.pulse_radius = 0.0
        self.pulse_alpha = 0.0
        self.is_landed = False

    def init_canvas(self, width: int, height: int):
        self.canvas_w = width
        self.canvas_h = height
        self.target_y = height / 2.0 - 90.0
        self.reset()

    def start_anim(self):
        if not self.timer.isActive():
            self.timer.start(16)  # 60 FPS (16ms)

    def stop_anim(self):
        self.timer.stop()

    def _on_tick(self):
        if not self.is_landed:
            if self.leaf_y < self.target_y:
                self.leaf_y += self.vy
                self.sway_phase += self.sway_freq
                self.leaf_x = self.x_center + math.sin(self.sway_phase) * self.sway_amplitude
                self.rotation += math.cos(self.sway_phase) * 1.6
            else:
                self.leaf_y = self.target_y
                self.leaf_x = self.x_center
                self.rotation = 0.0
                self.is_landed = True
                self.pulse_radius = 20.0
                self.pulse_alpha = 0.30
        else:
            # Expand pulse aura gently on landing
            if self.pulse_alpha > 0.01:
                self.pulse_radius += 1.8
                self.pulse_alpha -= 0.008
            else:
                self.pulse_alpha = 0.0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Draw landing pulse aura ring
        if self.pulse_alpha > 0.0:
            p_color = QColor(34, 197, 94, int(self.pulse_alpha * 255))
            painter.setPen(QPen(p_color, 2.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(self.x_center, self.target_y), self.pulse_radius, self.pulse_radius / 2.0)

        # Draw main hero falling leaf
        painter.save()
        painter.translate(self.leaf_x, self.leaf_y)
        painter.rotate(self.rotation)
        draw_leaf_shape(painter, self.size, QColor(34, 197, 94, 240))
        painter.restore()


class SplashScreen(QWidget):
    """
    App Startup Splash Screen with single aesthetic falling logo leaf animation.
    """
    animation_finished = pyqtSignal()

    def __init__(self, parent=None, duration_ms=3000):
        super().__init__(parent)
        self.duration_ms = duration_ms
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # Single Falling Leaf Canvas Widget
        self.leaf_canvas = SingleLeafCanvasWidget(self)
        self.leaf_canvas.resize(1024, 600)

        # Center Container Box
        self.center_box = QFrame(self)
        self.center_box.setFixedSize(500, 300)
        self.center_box.setStyleSheet("background: transparent; border: none;")

        cb_layout = QVBoxLayout(self.center_box)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_layout.setSpacing(12)

        # 1. Spacer for logo position
        self.logo_spacer = QFrame(self.center_box)
        self.logo_spacer.setFixedHeight(64)
        self.logo_spacer.setStyleSheet("background: transparent;")

        # 2. Title Label
        self.title_label = QLabel("PROJECT KISAN", self.center_box)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: 26px;
            font-weight: 800;
            letter-spacing: 2px;
        """)

        self.title_opacity = QGraphicsOpacityEffect(self.title_label)
        self.title_label.setGraphicsEffect(self.title_opacity)
        self.title_opacity.setOpacity(0.0)

        # 3. Subtitle / Tagline
        self.sub_label = QLabel("AI Powered • Offline • For Better Farming", self.center_box)
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet(f"""
            color: {COLOR_PRIMARY_ACCENT};
            font-family: {FONT_FAMILY};
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 1px;
        """)

        self.sub_opacity = QGraphicsOpacityEffect(self.sub_label)
        self.sub_label.setGraphicsEffect(self.sub_opacity)
        self.sub_opacity.setOpacity(0.0)

        # 4. Animated Progress Bar
        self.progress_bar = QProgressBar(self.center_box)
        self.progress_bar.setFixedWidth(280)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #121c12;
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_PRIMARY_ACCENT};
                border-radius: 2px;
            }}
        """)

        self.progress_opacity = QGraphicsOpacityEffect(self.progress_bar)
        self.progress_bar.setGraphicsEffect(self.progress_opacity)
        self.progress_opacity.setOpacity(0.0)

        cb_layout.addWidget(self.logo_spacer)
        cb_layout.addWidget(self.title_label)
        cb_layout.addWidget(self.sub_label)
        cb_layout.addSpacing(10)
        cb_layout.addWidget(self.progress_bar)

        layout.addWidget(self.center_box)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self.leaf_canvas.resize(w, h)
        self.leaf_canvas.init_canvas(w, h)

    def start_splash_animation(self):
        """Start single falling leaf animation and reveal timer."""
        w, h = self.width() or 1024, self.height() or 600
        self.leaf_canvas.init_canvas(w, h)
        self.leaf_canvas.start_anim()

        self.progress_bar.setValue(0)
        self.title_opacity.setOpacity(0.0)
        self.sub_opacity.setOpacity(0.0)
        self.progress_opacity.setOpacity(0.0)

        # Smooth title and progress bar fade-in group
        self.anim_group = QParallelAnimationGroup(self)

        anim_title = QPropertyAnimation(self.title_opacity, b"opacity")
        anim_title.setDuration(1200)
        anim_title.setStartValue(0.0)
        anim_title.setEndValue(1.0)
        anim_title.setEasingCurve(QEasingCurve.OutCubic)

        anim_sub = QPropertyAnimation(self.sub_opacity, b"opacity")
        anim_sub.setDuration(1400)
        anim_sub.setStartValue(0.0)
        anim_sub.setEndValue(1.0)
        anim_sub.setEasingCurve(QEasingCurve.OutCubic)

        anim_prog = QPropertyAnimation(self.progress_opacity, b"opacity")
        anim_prog.setDuration(800)
        anim_prog.setStartValue(0.0)
        anim_prog.setEndValue(1.0)

        self.anim_group.addAnimation(anim_title)
        self.anim_group.addAnimation(anim_sub)
        self.anim_group.addAnimation(anim_prog)

        self.anim_group.start()

        # Progress bar timer over 3000ms duration
        self.timer_step = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_timer.start(30)

    def _update_progress(self):
        self.timer_step += 1
        percentage = int((self.timer_step / 100.0) * 100)
        self.progress_bar.setValue(percentage)

        if self.timer_step >= 100:
            self.progress_timer.stop()
            self.leaf_canvas.stop_anim()
            QTimer.singleShot(200, self._on_finish)

    def _on_finish(self):
        self.animation_finished.emit()
