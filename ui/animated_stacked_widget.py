"""
Animated QStackedWidget implementation providing smooth fade transitions.
Optimized 60 FPS cubic easing for zero lag responsiveness.
"""

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QStackedWidget


class AnimatedStackedWidget(QStackedWidget):
    """
    QStackedWidget subclass that provides smooth animated fade transitions
    between page widgets.
    """

    def __init__(self, parent=None, duration=160):
        super().__init__(parent)
        self.duration = duration
        self._is_animating = False
        self.fade_anim = None
        self.opacity_effect = None

    def set_current_index_animated(self, index: int):
        """Smoothly fade transition to target index."""
        if index == self.currentIndex() or index < 0 or index >= self.count():
            return

        # Stop previous animation if running
        if self._is_animating and self.fade_anim:
            self.fade_anim.stop()

        next_widget = self.widget(index)
        if not next_widget:
            return

        # Set up opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Switch stack index
        self.setCurrentIndex(index)

        # Animate opacity 0.0 -> 1.0 with OutCubic easing
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(self.duration)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._is_animating = True

        def cleanup():
            self._is_animating = False
            if next_widget and next_widget.graphicsEffect() == self.opacity_effect:
                next_widget.setGraphicsEffect(None)

        self.fade_anim.finished.connect(cleanup)
        self.fade_anim.start()
