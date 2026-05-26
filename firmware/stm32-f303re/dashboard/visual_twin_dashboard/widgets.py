from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from .models import (
    FAULT_NONE,
    PROTECTION_IMBALANCE_V,
    PROTECTION_OVERCURRENT_A,
    PROTECTION_OVERVOLTAGE_V,
    PROTECTION_UNDERVOLTAGE_V,
    STATE_NAMES,
    TelemetryFrame,
)


BG = QColor("#0d0f10")
PANEL = QColor("#17191b")
SURFACE = QColor("#202326")
TEXT = QColor("#e1e3df")
MUTED = QColor("#8f9693")
ACCENT = QColor("#7aa89f")
BLUE = QColor("#8aa8bd")
YELLOW = QColor("#b69b57")
RED = QColor("#c45b5b")
GREEN = QColor("#78a577")


class FaultBadge(QLabel):
    def __init__(self) -> None:
        super().__init__("NONE")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(150)
        self.set_faults(FAULT_NONE)

    def set_faults(self, bits: int, text: str = "NONE") -> None:
        if bits == FAULT_NONE:
            self.setStyleSheet(
                "QLabel { background:#1b2a21; color:#c7e0cf; border:1px solid #405c49; "
                "border-radius:3px; padding:6px 10px; font-weight:700; }"
            )
        else:
            self.setStyleSheet(
                "QLabel { background:#3a2020; color:#f0cece; border:1px solid #8d5555; "
                "border-radius:3px; padding:6px 10px; font-weight:800; }"
            )
        self.setText(text)


class FsmWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.state = "IDLE"
        self.setFixedHeight(108)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_state(self, state: str) -> None:
        self.state = state
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(720, 108)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override.
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), PANEL)
        painter.setPen(TEXT)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(16, 22, "FSM State Flow")

        margin = 26
        top = 40
        box_w = max(92, (self.width() - margin * 2 - 54 * 4) // 5)
        box_h = 38
        gap = (self.width() - margin * 2 - box_w * 5) / 4.0
        centers = []

        for index, name in enumerate(STATE_NAMES):
            x = margin + index * (box_w + gap)
            rect = QRectF(x, top, box_w, box_h)
            active = name == self.state
            color = RED if name == "FAULT" and active else ACCENT if active else SURFACE
            painter.setPen(QPen(color.lighter(130), 2 if active else 1))
            painter.setBrush(color)
            painter.drawRoundedRect(rect, 3, 3)
            painter.setPen(TEXT if active else QColor("#c8cbc7"))
            painter.drawText(rect, Qt.AlignCenter, name)
            centers.append(QPointF(rect.right(), rect.center().y()))

        painter.setPen(QPen(MUTED, 2))
        for index in range(4):
            start = centers[index] + QPointF(8, 0)
            end = QPointF(margin + (index + 1) * (box_w + gap) - 8, centers[index].y())
            painter.drawLine(start, end)
            self._draw_arrow(painter, end)

        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(MUTED)
        painter.drawText(28, self.height() - 12, "START gates PRECHARGE; RUN checks protection after sensor scans; faults latch until CLEAR.")

    @staticmethod
    def _draw_arrow(painter: QPainter, tip: QPointF) -> None:
        path = QPainterPath()
        path.moveTo(tip)
        path.lineTo(tip + QPointF(-8, -5))
        path.lineTo(tip + QPointF(-8, 5))
        path.closeSubpath()
        painter.fillPath(path, MUTED)


class PwmTwinWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.frame = TelemetryFrame(0, "IDLE", "FULL", 0, 50.0, 50.0, 0.0, 0)
        self.phase = 0.0
        self.running = False
        self.setFixedHeight(136)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_frame(self, frame: TelemetryFrame) -> None:
        self.frame = frame
        self.running = frame.state in ("PRECHARGE", "RUN")
        if not self.running:
            self.phase = 0.0
        self.update()

    def set_running(self, running: bool) -> None:
        self.running = running
        if not running:
            self.phase = 0.0
        self.update()

    def animate(self, step: float = 0.18) -> None:
        if not self.running:
            return
        self.phase = (self.phase + step) % (2.0 * math.pi)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override.
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), PANEL)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.setPen(TEXT)
        painter.drawText(16, 22, "Predicted Output Waveform")

        level = self.frame.level
        wave_rect = QRectF(20, 36, max(220, self.width() - 40), 72)
        self._draw_waveform(painter, wave_rect)

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(MUTED)
        state_text = "holding" if not self.running else "tracking"
        painter.drawText(20, self.height() - 12, f"{state_text} telemetry level: {self._level_label(level)}")

    def _draw_waveform(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(QPen(QColor("#303436"), 1))
        painter.setBrush(QColor("#111314"))
        painter.drawRoundedRect(rect, 3, 3)
        mid = rect.center().y()
        level_marks = [(-2, "-2Vdc"), (-1, "-Vdc"), (0, "0"), (1, "+Vdc"), (2, "+2Vdc")]
        painter.setFont(QFont("Segoe UI", 8))
        for raw_level, label in level_marks:
            offset = raw_level / 2.0
            y_pos = mid - offset * (rect.height() * 0.38)
            painter.setPen(QPen(QColor("#2a2e30"), 1, Qt.DashLine))
            painter.drawLine(QPointF(rect.left() + 1, y_pos), QPointF(rect.right() - 1, y_pos))
            painter.setPen(MUTED)
            painter.drawText(QRectF(rect.left() + 8, y_pos - 10, 70, 18), Qt.AlignLeft | Qt.AlignVCenter, label)

        points: list[QPointF] = []
        for i in range(int(rect.width())):
            t = self.phase + i * 0.05
            value = math.sin(t)
            if value >= 0.6:
                quantized = 1.0
            elif value >= 0.2:
                quantized = 0.5
            elif value <= -0.6:
                quantized = -1.0
            elif value <= -0.2:
                quantized = -0.5
            else:
                quantized = 0.0
            y_pos = mid - quantized * (rect.height() * 0.38)
            points.append(QPointF(rect.left() + i, y_pos))
        painter.setPen(QPen(YELLOW, 2))
        for a, b in zip(points, points[1:]):
            painter.drawLine(a, b)

        marker_x = rect.left() + rect.width() * 0.18
        marker_y = mid - (self.frame.level / 2.0) * (rect.height() * 0.38)
        painter.setPen(QPen(ACCENT, 2))
        painter.drawLine(QPointF(marker_x, rect.top() + 6), QPointF(marker_x, rect.bottom() - 6))
        painter.setBrush(ACCENT)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(marker_x, marker_y), 4, 4)

    @staticmethod
    def _level_label(level: int) -> str:
        labels = {
            -2: "negative full step",
            -1: "negative half step",
            0: "zero step",
            1: "positive half step",
            2: "positive full step",
        }
        return labels.get(level, "unknown step")


class ModulationWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.frame = TelemetryFrame(0, "IDLE", "FULL", 0, 50.0, 50.0, 0.0, 0)
        self.phase = 0.0
        self.running = False
        self.modulation_index = 0.95
        self.setFixedHeight(136)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_frame(self, frame: TelemetryFrame) -> None:
        self.frame = frame
        self.modulation_index = max(0.0, min(0.95, frame.modulation_index))
        self.running = frame.state in ("PRECHARGE", "RUN")
        if not self.running:
            self.phase = 0.0
        self.update()

    def set_running(self, running: bool) -> None:
        self.running = running
        if not running:
            self.phase = 0.0
        self.update()

    def animate(self, step: float = 0.11) -> None:
        if not self.running:
            return
        self.phase = (self.phase + step) % (2.0 * math.pi)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override.
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), PANEL)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.setPen(TEXT)
        painter.drawText(16, 22, "Sine Reference vs Carrier")

        plot_rect = QRectF(20, 36, max(220, self.width() - 40), 72)
        self._draw_plot(painter, plot_rect)

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(MUTED)
        state_text = "PWM disabled" if self.frame.state in ("IDLE", "FAULT", "BOOT") else "PWM timing active"
        painter.drawText(
            20,
            self.height() - 12,
            f"{state_text}; modulation index {self.modulation_index:.2f}",
        )

    def _draw_plot(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(QPen(QColor("#303436"), 1))
        painter.setBrush(QColor("#111314"))
        painter.drawRoundedRect(rect, 3, 3)

        mid = rect.center().y()
        amp = rect.height() * 0.38
        painter.setFont(QFont("Segoe UI", 8))

        for value, label in ((0.6, "+T2"), (0.2, "+T1"), (0.0, "0"), (-0.2, "-T1"), (-0.6, "-T2")):
            y_pos = mid - value * amp
            painter.setPen(QPen(QColor("#2a2e30"), 1, Qt.DashLine))
            painter.drawLine(QPointF(rect.left() + 1, y_pos), QPointF(rect.right() - 1, y_pos))
            painter.setPen(MUTED)
            painter.drawText(QRectF(rect.left() + 8, y_pos - 9, 40, 16), Qt.AlignLeft | Qt.AlignVCenter, label)

        carrier_points: list[QPointF] = []
        sine_points: list[QPointF] = []
        quantized_points: list[QPointF] = []
        width = max(1, int(rect.width()))
        for i in range(width):
            x = rect.left() + i
            t = self.phase + i * 0.045
            sine = self.modulation_index * math.sin(t)
            carrier = self._triangle((t / (2.0 * math.pi)) * 8.0)
            quantized = self._quantized_reference(sine)
            carrier_points.append(QPointF(x, mid - carrier * amp))
            sine_points.append(QPointF(x, mid - sine * amp))
            quantized_points.append(QPointF(x, mid - quantized * amp))

        painter.setPen(QPen(QColor("#5f6564"), 1))
        for a, b in zip(carrier_points, carrier_points[1:]):
            painter.drawLine(a, b)

        painter.setPen(QPen(BLUE, 2))
        for a, b in zip(sine_points, sine_points[1:]):
            painter.drawLine(a, b)

        painter.setPen(QPen(YELLOW, 2))
        for a, b in zip(quantized_points, quantized_points[1:]):
            painter.drawLine(a, b)

        painter.setPen(QPen(ACCENT, 1))
        marker_x = rect.left() + rect.width() * 0.18
        painter.drawLine(QPointF(marker_x, rect.top() + 6), QPointF(marker_x, rect.bottom() - 6))

        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(BLUE)
        painter.drawText(QRectF(rect.right() - 155, rect.top() + 8, 145, 16), Qt.AlignRight, "sine reference")
        painter.setPen(QColor("#7b817f"))
        painter.drawText(QRectF(rect.right() - 155, rect.top() + 25, 145, 16), Qt.AlignRight, "triangle carrier")
        painter.setPen(YELLOW)
        painter.drawText(QRectF(rect.right() - 155, rect.top() + 42, 145, 16), Qt.AlignRight, "5-level decision")

    @staticmethod
    def _triangle(value: float) -> float:
        fraction = value - math.floor(value)
        if fraction < 0.5:
            return -1.0 + 4.0 * fraction
        return 3.0 - 4.0 * fraction

    @staticmethod
    def _quantized_reference(value: float) -> float:
        if value >= 0.6:
            return 1.0
        if value >= 0.2:
            return 0.5
        if value <= -0.6:
            return -1.0
        if value <= -0.2:
            return -0.5
        return 0.0


class SensorGauge(QWidget):
    def __init__(self, title: str, unit: str, minimum: float, maximum: float) -> None:
        super().__init__()
        self.title = title
        self.unit = unit
        self.minimum = minimum
        self.maximum = maximum
        self.value: Optional[float] = None
        self.warning_low: Optional[float] = None
        self.warning_high: Optional[float] = None
        self.setFixedHeight(66)

    def set_thresholds(self, low: Optional[float] = None, high: Optional[float] = None) -> None:
        self.warning_low = low
        self.warning_high = high

    def set_value(self, value: Optional[float]) -> None:
        self.value = value
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override.
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), PANEL)
        painter.setPen(TEXT)
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(12, 18, self.title)

        value_text = "NAN" if self.value is None else f"{self.value:.2f} {self.unit}"
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.setPen(RED if self._is_alarm() else TEXT)
        painter.drawText(12, 42, value_text)

        bar = QRectF(12, 50, self.width() - 24, 8)
        painter.setPen(Qt.NoPen)
        painter.setBrush(SURFACE)
        painter.drawRoundedRect(bar, 3, 3)

        if self.value is not None:
            fraction = (self.value - self.minimum) / (self.maximum - self.minimum)
            fraction = max(0.0, min(1.0, fraction))
            fill = QRectF(bar.left(), bar.top(), bar.width() * fraction, bar.height())
            painter.setBrush(RED if self._is_alarm() else BLUE)
            painter.drawRoundedRect(fill, 3, 3)

        painter.setBrush(YELLOW)
        for threshold in (self.warning_low, self.warning_high):
            if threshold is None:
                continue
            pos = (threshold - self.minimum) / (self.maximum - self.minimum)
            x = bar.left() + max(0.0, min(1.0, pos)) * bar.width()
            painter.drawRect(QRectF(x - 1, bar.top() - 3, 2, bar.height() + 6))

    def _is_alarm(self) -> bool:
        if self.value is None:
            return False
        if self.warning_low is not None and self.value < self.warning_low:
            return True
        if self.warning_high is not None and self.value > self.warning_high:
            return True
        return False


class ImbalanceGauge(SensorGauge):
    def __init__(self) -> None:
        super().__init__("DC imbalance", "V", 0.0, 20.0)
        self.set_thresholds(high=PROTECTION_IMBALANCE_V)


def make_sensor_gauges() -> tuple[SensorGauge, SensorGauge, SensorGauge, ImbalanceGauge]:
    vdc1 = SensorGauge("DC bus 1", "V", 0.0, 70.0)
    vdc1.set_thresholds(PROTECTION_UNDERVOLTAGE_V, PROTECTION_OVERVOLTAGE_V)
    vdc2 = SensorGauge("DC bus 2", "V", 0.0, 70.0)
    vdc2.set_thresholds(PROTECTION_UNDERVOLTAGE_V, PROTECTION_OVERVOLTAGE_V)
    iout = SensorGauge("Output current", "A", -20.0, 20.0)
    iout.set_thresholds(-PROTECTION_OVERCURRENT_A, PROTECTION_OVERCURRENT_A)
    return vdc1, vdc2, iout, ImbalanceGauge()
