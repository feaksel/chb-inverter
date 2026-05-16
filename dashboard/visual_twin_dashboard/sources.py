from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from .models import TelemetryFrame
from .protocol import parse_line
from .sim import SimController, mode_name_from_id

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - exercised by manual app startup.
    serial = None
    list_ports = None


class BaseSource(QObject):
    frame_received = Signal(object)
    event_received = Signal(str, str)
    connection_changed = Signal(str)

    def send_command(self, command: str) -> None:
        raise NotImplementedError


class SimSource(BaseSource):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.controller = SimController()
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._tick)

    def start(self) -> None:
        if not self.timer.isActive():
            self.timer.start()
        self.connection_changed.emit("Simulator running")

    def stop(self) -> None:
        self.timer.stop()
        self.connection_changed.emit("Simulator stopped")

    def play_scenario(self, key: str) -> None:
        message = self.controller.run_scenario(key)
        self.event_received.emit("SIM", message)
        self.start()
        self._tick()

    def normalize(self) -> None:
        self.controller.normalize_fault_condition()
        self.event_received.emit("SIM", "Fault condition normalized")

    def send_command(self, command: str) -> None:
        text = command.strip().upper()
        if text == "START":
            reply = self.controller.start()
        elif text == "STOP":
            reply = self.controller.stop()
        elif text == "CLEAR":
            reply = self.controller.clear()
        elif text == "STATUS":
            reply = "STATUS"
        elif text == "HELP":
            reply = ("START STOP CLEAR MODE 0..5 STATUS HELP MI 0.0..0.95 "
                     "RESCAN MOD STAIR|PSC FSW <hz> BRIDGE BOTH|B1|B2 "
                     "FFUND <hz> CONFIG")
        elif text == "RESCAN":
            reply = self.controller.rescan()
        elif text == "CONFIG":
            reply = self.controller.config_summary()
        elif text.startswith("MODE "):
            try:
                reply = self.controller.set_mode(mode_name_from_id(int(text.split()[1])))
            except (IndexError, ValueError):
                reply = "MODE_SENSOR_UNAVAILABLE"
        elif text.startswith("MI "):
            try:
                reply = self.controller.set_modulation_index(float(text.split()[1]))
            except (IndexError, ValueError):
                reply = "MI_RANGE_0_TO_0_95"
        elif text.startswith("MOD "):
            reply = self.controller.set_modulator(text.split(maxsplit=1)[1].strip())
        elif text.startswith("BRIDGE "):
            reply = self.controller.set_bridge(text.split(maxsplit=1)[1].strip())
        elif text.startswith("FSW "):
            try:
                reply = self.controller.set_switching_freq(int(float(text.split()[1])))
            except (IndexError, ValueError):
                reply = "FSW_RANGE_100_TO_20000"
        elif text.startswith("FFUND "):
            try:
                reply = self.controller.set_fundamental_freq(float(text.split()[1]))
            except (IndexError, ValueError):
                reply = "FFUND_RANGE_10_TO_400"
        else:
            reply = "UNKNOWN_COMMAND"
        channel = "SIM-ACK" if reply == text or reply.startswith(("MODE ", "MI ")) else "SIM"
        self.event_received.emit(channel, reply)
        self._tick()

    def _tick(self) -> None:
        frame = self.controller.step(self.timer.interval() if self.timer.isActive() else 50)
        self.frame_received.emit(frame)


class SerialSource(BaseSource):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.port = None
        self.rx_text = ""
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.poll)

    @staticmethod
    def available_ports() -> list[str]:
        if list_ports is None:
            return []
        return [port.device for port in list_ports.comports()]

    def connect_port(self, port_name: str, baudrate: int = 115200) -> bool:
        if serial is None:
            self.event_received.emit("ERROR", "pyserial is not installed")
            self.connection_changed.emit("Serial unavailable")
            return False
        self.disconnect_port()
        try:
            self.port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=0,
                write_timeout=0.2,
            )
        except serial.SerialException as exc:
            self.event_received.emit("ERROR", str(exc))
            self.connection_changed.emit("Disconnected")
            return False

        self.rx_text = ""
        self.timer.start()
        self.connection_changed.emit(f"Connected to {port_name}")
        self.event_received.emit("SERIAL", f"Connected {port_name} @ {baudrate}")
        return True

    def disconnect_port(self) -> None:
        self.timer.stop()
        if self.port is not None:
            try:
                self.port.close()
            except Exception as exc:  # pragma: no cover - defensive close path.
                self.event_received.emit("ERROR", str(exc))
        self.port = None
        self.connection_changed.emit("Disconnected")

    def send_command(self, command: str) -> None:
        if self.port is None or not self.port.is_open:
            self.event_received.emit("ERROR", "Serial port is not connected")
            return
        text = command.strip()
        if not text:
            return
        try:
            self.port.write((text + "\r\n").encode("ascii"))
            self.event_received.emit("TX", text)
        except serial.SerialException as exc:
            self.event_received.emit("ERROR", str(exc))
            self.disconnect_port()

    def poll(self) -> None:
        if self.port is None or not self.port.is_open:
            return
        try:
            waiting = self.port.in_waiting
            if waiting <= 0:
                return
            chunk = self.port.read(waiting).decode("ascii", errors="replace")
        except serial.SerialException as exc:
            self.event_received.emit("ERROR", str(exc))
            self.disconnect_port()
            return

        self.rx_text += chunk
        while "\n" in self.rx_text:
            line, self.rx_text = self.rx_text.split("\n", 1)
            self._handle_line(line.strip("\r"))

    def _handle_line(self, line: str) -> None:
        parsed = parse_line(line, source="serial")
        if parsed.kind == "telemetry" and parsed.frame is not None:
            self.frame_received.emit(parsed.frame)
            if not parsed.checksum_valid:
                self.event_received.emit("WARN", f"Bad checksum: {parsed.raw}")
            return
        label = parsed.kind.upper()
        self.event_received.emit(label, parsed.message or parsed.raw)


class ReplaySource(BaseSource):
    def __init__(self, path: Path, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.path = path
        self.lines: list[str] = []
        self.index = 0
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._tick)

    def load(self) -> None:
        self.lines = self.path.read_text(encoding="utf-8").splitlines()
        self.index = 0
        self.event_received.emit("REPLAY", f"Loaded {len(self.lines)} lines from {self.path}")

    def start(self) -> None:
        if not self.lines:
            self.load()
        self.timer.start()
        self.connection_changed.emit("Replay running")

    def stop(self) -> None:
        self.timer.stop()
        self.connection_changed.emit("Replay stopped")

    def send_command(self, command: str) -> None:
        self.event_received.emit("REPLAY", f"Ignored command: {command.strip()}")

    def _tick(self) -> None:
        if not self.lines:
            return
        parsed = parse_line(self.lines[self.index], source="replay")
        self.index = (self.index + 1) % len(self.lines)
        if parsed.kind == "telemetry" and parsed.frame is not None:
            self.frame_received.emit(parsed.frame)
        else:
            self.event_received.emit(parsed.kind.upper(), parsed.message or parsed.raw)

