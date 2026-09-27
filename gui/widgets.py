"""Animated voice assistant avatar rendered with QPainter.

Qt QSS lacks CSS @keyframes, so the halo animation is driven by a looping
QVariantAnimation that produces a 0..1 phase value each frame; paintEvent
maps the phase to a rotating arc (processing) or a pulsing glow (speaking).
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

_CIRCLE_COLOR_TOP = QColor("#6ba3d6")
_CIRCLE_COLOR_BOTTOM = QColor("#1e3a5f")
_HALO_COLOR = QColor("#4da6ff")

_VALID_STATES = frozenset({"idle", "listening", "processing", "speaking"})


class VoiceAssistantAvatar(QWidget):
    def __init__(self, diameter=220, margin=20, parent=None):
        super().__init__(parent)
        self._state = "idle"
        self._diameter = diameter
        self._margin = margin
        self.setFixedSize(diameter, diameter)
        self.setMinimumSize(diameter, diameter)

        self._phase = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1600)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._on_tick)

    def _on_tick(self, value):
        self._phase = float(value)
        self.update()

    def set_state(self, state: str):
        if state not in _VALID_STATES:
            raise ValueError(
                f"Invalid state {state!r}; expected one of {sorted(_VALID_STATES)}"
            )
        self._state = state
        if state in ("processing", "speaking"):
            self._phase = 0.0
            if not self._anim.state() == self._anim.State.Running:
                self._anim.start()
        else:
            self._anim.stop()
            self._phase = 0.0
        self.update()

    @property
    def state(self):
        return self._state

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # دایره رو با مارجین از طرفین رسم می‌کنیم
        inner = self._diameter - 2 * self._margin
        rect = QRectF(self._margin, self._margin, inner, inner)
        center = QPointF(rect.center())
        radius = inner / 2.0

        self._paint_halo(p, center, radius)
        self._paint_circle(p, rect)

    def _paint_circle(self, p: QPainter, rect: QRectF):
        grad = QRadialGradient(rect.center(), rect.width() / 2)
        grad.setColorAt(0.0, _CIRCLE_COLOR_TOP)
        grad.setColorAt(0.6, QColor("#3a6ea5"))
        grad.setColorAt(1.0, _CIRCLE_COLOR_BOTTOM)
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(255, 255, 255, 32), 2))
        p.drawEllipse(rect)

    def _paint_halo(self, p: QPainter, center: QPointF, radius: float):
        if self._state == "idle":
            return

        if self._state == "listening":
            self._paint_glow(p, center, radius, intensity=0.75, radius_override=1.08)
            return

        if self._state == "processing":
            self._paint_arc(p, center, radius, self._phase * 360.0)
            return

        if self._state == "speaking":
            pulse = 0.5 * (1.0 + math.sin(self._phase * 2.0 * math.pi))
            self._paint_glow(p, center, radius, intensity=0.4 + 0.5 * pulse,
                             radius_override=1.02 + 0.10 * pulse)
            return

    def _paint_glow(self, p: QPainter, center: QPointF, radius: float,
                    intensity: float, radius_override: float):
        outer = radius * radius_override
        ring_radius = radius * 0.82 + (outer - radius) * 0.5

        glow = QRadialGradient(center, outer)
        glow.setColorAt(0.0, _HALO_COLOR)
        glow.setColorAt(0.85, _HALO_COLOR)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(center, outer, outer)

        pen = QPen(_HALO_COLOR)
        pen.setWidthF(6.0)
        pen_alpha = int(255 * max(0.0, min(1.0, intensity)))
        pen.setColor(QColor(_HALO_COLOR.red(), _HALO_COLOR.green(),
                            _HALO_COLOR.blue(), pen_alpha))
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, ring_radius, ring_radius)

    def _paint_arc(self, p: QPainter, center: QPointF, radius: float, angle_deg: float):
        ring_radius = radius * 0.92
        pen = QPen(_HALO_COLOR)
        pen.setWidthF(8.0)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        span = 100.0
        start = -(angle_deg + 90.0) % 360.0
        p.drawArc(
            int(center.x() - ring_radius), int(center.y() - ring_radius),
            int(ring_radius * 2), int(ring_radius * 2),
            int(start * 16), int(-span * 16),
        )

    def sizeHint(self):
        return self.minimumSize()
