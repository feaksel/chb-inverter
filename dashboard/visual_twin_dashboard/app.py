from __future__ import annotations

import math
import sys
from dataclasses import replace
from typing import List

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import pyqtgraph as pg
except ImportError as exc:  # pragma: no cover - app startup dependency check.
    raise RuntimeError("pyqtgraph is required; install dashboard/requirements.txt") from exc

from .models import MODE_IDS, MODE_LABELS, TelemetryFrame
from .sim import SCENARIOS
from .sources import SerialSource, SimSource
from .widgets import FaultBadge, FsmWidget, ModulationWidget, PwmTwinWidget, make_sensor_gauges


class DashboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("5-Level CHB Visual Twin Dashboard")
        self.resize(1440, 960)
        self.setMinimumSize(1120, 780)

        self.sim_source = SimSource(self)
        self.serial_source = SerialSource(self)
        self.current_source_name = "Simulator"
        self.last_frame = TelemetryFrame(0, "IDLE", "FULL", 0, 50.0, 50.0, 0.0, 0)
        self.history_limit = 600
        self.t_history: List[float] = []
        self.vdc1_history: List[float] = []
        self.vdc2_history: List[float] = []
        self.iout_history: List[float] = []
        self.plot_window_seconds = 12.0
        self.current_modulation_index = 0.95

        self._build_ui()
        self._connect_sources()
        self._refresh_ports()
        self._set_source("Simulator")

        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(33)
        self.animation_timer.timeout.connect(self._animate_visuals)
        self.animation_timer.start()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.setCentralWidget(root)

        layout.addWidget(self._make_top_bar())

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        self.fsm_widget = FsmWidget()
        self.modulation_widget = ModulationWidget()
        self.pwm_twin = PwmTwinWidget()
        self.visual_tabs = QTabWidget()
        self.visual_tabs.addTab(self.modulation_widget, "Modulation")
        self.visual_tabs.addTab(self.pwm_twin, "Output steps")
        self.visual_tabs.setFixedHeight(176)
        plot_panel = self._make_plot_panel()
        center_layout.addWidget(self.fsm_widget)
        center_layout.addWidget(self.visual_tabs)
        center_layout.addWidget(plot_panel, 1)

        right = self._make_sensor_panel()
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        bottom_panel = self._make_bottom_panel()
        bottom_panel.setMinimumHeight(340)
        bottom_panel.setMaximumHeight(560)
        main_splitter.addWidget(splitter)
        main_splitter.addWidget(bottom_panel)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setSizes([520, 440])
        layout.addWidget(main_splitter, 1)
        self._apply_style()

    def _make_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self.source_combo = QComboBox()
        self.source_combo.addItems(["Simulator", "Live serial"])
        self.source_combo.currentTextChanged.connect(self._set_source)

        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton("Refresh")
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._toggle_serial)
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setMinimumWidth(180)

        self.state_label = QLabel("State: IDLE")
        self.mode_label = QLabel("Mode: FULL")
        self.fault_badge = FaultBadge()
        self.follow_plot = QCheckBox("Follow graph")
        self.follow_plot.setChecked(True)

        layout.addWidget(QLabel("Source"))
        layout.addWidget(self.source_combo)
        layout.addSpacing(8)
        layout.addWidget(QLabel("COM"))
        layout.addWidget(self.port_combo)
        layout.addWidget(self.refresh_ports_btn)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.connection_label, 1)
        layout.addWidget(self.state_label)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.follow_plot)
        layout.addWidget(QLabel("Fault"))
        layout.addWidget(self.fault_badge)
        return bar

    def _make_plot_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("plotPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(2.0, 120.0)
        self.window_spin.setDecimals(0)
        self.window_spin.setSuffix(" s")
        self.window_spin.setValue(self.plot_window_seconds)
        self.window_spin.valueChanged.connect(self._set_plot_window)
        zoom_in_btn = QPushButton("Zoom in")
        zoom_in_btn.clicked.connect(lambda: self._zoom_plot(0.5))
        zoom_out_btn = QPushButton("Zoom out")
        zoom_out_btn.clicked.connect(lambda: self._zoom_plot(2.0))
        reset_btn = QPushButton("Reset view")
        reset_btn.clicked.connect(self._reset_plot_view)
        controls.addWidget(QLabel("Sensor graph"))
        controls.addStretch(1)
        controls.addWidget(QLabel("Window"))
        controls.addWidget(self.window_spin)
        controls.addWidget(zoom_in_btn)
        controls.addWidget(zoom_out_btn)
        controls.addWidget(reset_btn)

        self.plot = self._make_plot()
        layout.addLayout(controls)
        layout.addWidget(self.plot, 1)
        return panel

    def _make_plot(self):
        plot = pg.PlotWidget()
        plot.setBackground("#17191b")
        plot.showGrid(x=True, y=True, alpha=0.16)
        plot.setLabel("left", "Sensors")
        plot.setLabel("bottom", "time", units="s")
        plot.addLegend(offset=(10, 10))
        plot.setMinimumHeight(120)
        plot.setYRange(-22.0, 70.0, padding=0.02)
        plot.setMouseEnabled(x=True, y=True)
        plot.getAxis("left").setPen(pg.mkPen("#777d7b"))
        plot.getAxis("bottom").setPen(pg.mkPen("#777d7b"))
        self.vdc1_curve = plot.plot(pen=pg.mkPen("#8aa8bd", width=2), name="vdc1")
        self.vdc2_curve = plot.plot(pen=pg.mkPen("#7aa89f", width=2), name="vdc2")
        self.iout_curve = plot.plot(pen=pg.mkPen("#b69b57", width=2), name="iout")
        try:
            plot.getViewBox().sigRangeChangedManually.connect(self._plot_manually_changed)
        except AttributeError:
            pass
        return plot

    def _make_sensor_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.vdc1_gauge, self.vdc2_gauge, self.iout_gauge, self.imbalance_gauge = make_sensor_gauges()
        for gauge in (self.vdc1_gauge, self.vdc2_gauge, self.iout_gauge, self.imbalance_gauge):
            layout.addWidget(gauge)

        self.safety_box = QLabel("PC-only simulation: scenarios never write fake faults to firmware.")
        self.safety_box.setWordWrap(True)
        self.safety_box.setObjectName("safetyBox")
        layout.addWidget(self.safety_box)
        layout.addStretch(1)
        return panel

    def _make_bottom_panel(self) -> QWidget:
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._make_command_group(), 2)
        layout.addWidget(self._make_scenario_group(), 2)

        log_group = QGroupBox("Raw UART / Event Log")
        log_layout = QVBoxLayout(log_group)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(96)
        log_layout.addWidget(self.log)
        layout.addWidget(log_group, 3)
        return panel

    def _make_command_group(self) -> QGroupBox:
        group = QGroupBox("Controls")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.arm_live = QCheckBox("Arm live START")
        self.arm_live.stateChanged.connect(self._update_scenario_buttons)
        layout.addWidget(self.arm_live)

        # Two rows of command buttons so the labels aren't cramped: the
        # state-changing actions on top, the query/diagnostic commands below.
        action_commands = [
            ("START", self._send_start),
            ("STOP", lambda: self._send_command("STOP")),
            ("CLEAR", lambda: self._send_command("CLEAR")),
        ]
        query_commands = [
            ("STATUS", lambda: self._send_command("STATUS")),
            ("HELP", lambda: self._send_command("HELP")),
            ("RESCAN", lambda: self._send_command("RESCAN")),
            ("CONFIG", lambda: self._send_command("CONFIG")),
        ]
        for command_set in (action_commands, query_commands):
            command_row = QHBoxLayout()
            command_row.setSpacing(6)
            for label, handler in command_set:
                button = QPushButton(label)
                button.setMinimumHeight(30)
                button.clicked.connect(handler)
                command_row.addWidget(button)
            layout.addLayout(command_row)

        mode_row = QHBoxLayout()
        self.mode_combo = QComboBox()
        for mode in MODE_IDS:
            self.mode_combo.addItem(f"{mode} - {MODE_LABELS[mode]}", mode)
        self.mode_btn = QPushButton("Set mode")
        self.mode_btn.clicked.connect(self._send_mode)
        mode_row.addWidget(QLabel("Mode"))
        mode_row.addWidget(self.mode_combo, 1)
        mode_row.addWidget(self.mode_btn)
        layout.addLayout(mode_row)

        mi_row = QHBoxLayout()
        self.mi_spin = QDoubleSpinBox()
        self.mi_spin.setRange(0.0, 0.95)
        self.mi_spin.setSingleStep(0.05)
        self.mi_spin.setDecimals(2)
        self.mi_spin.setValue(0.95)
        self.mi_btn = QPushButton("Set MI")
        self.mi_btn.clicked.connect(lambda: self._send_command(f"MI {self.mi_spin.value():.2f}"))
        mi_row.addWidget(QLabel("MI"))
        mi_row.addWidget(self.mi_spin)
        mi_row.addWidget(self.mi_btn)

        self.normalize_btn = QPushButton("Normalize sim sensors")
        self.normalize_btn.clicked.connect(self._normalize_sim)
        mi_row.addWidget(self.normalize_btn)
        layout.addLayout(mi_row)

        mod_row = QHBoxLayout()
        self.mod_combo = QComboBox()
        self.mod_combo.addItems(["STAIR", "PSC", "STAIR_ALT"])
        self.mod_btn = QPushButton("Set Mod")
        self.mod_btn.clicked.connect(self._send_mod)
        mod_row.addWidget(QLabel("Modulator"))
        mod_row.addWidget(self.mod_combo, 1)
        mod_row.addWidget(self.mod_btn)
        layout.addLayout(mod_row)

        fsw_row = QHBoxLayout()
        self.fsw_combo = QComboBox()
        self.fsw_combo.setEditable(True)
        self.fsw_combo.addItems(["500", "1000", "2000", "5000", "10000"])
        self.fsw_combo.setCurrentText("500")
        self.fsw_btn = QPushButton("Set FSW")
        self.fsw_btn.clicked.connect(self._send_fsw)
        fsw_row.addWidget(QLabel("Sw Freq (Hz)"))
        fsw_row.addWidget(self.fsw_combo, 1)
        fsw_row.addWidget(self.fsw_btn)
        layout.addLayout(fsw_row)

        bridge_row = QHBoxLayout()
        self.bridge_combo = QComboBox()
        self.bridge_combo.addItems(["BOTH", "B1", "B2"])
        self.bridge_btn = QPushButton("Set Bridge")
        self.bridge_btn.clicked.connect(self._send_bridge)
        bridge_row.addWidget(QLabel("Bridge"))
        bridge_row.addWidget(self.bridge_combo, 1)
        bridge_row.addWidget(self.bridge_btn)
        layout.addLayout(bridge_row)

        ffund_row = QHBoxLayout()
        self.ffund_spin = QDoubleSpinBox()
        self.ffund_spin.setRange(10.0, 400.0)
        self.ffund_spin.setSingleStep(1.0)
        self.ffund_spin.setDecimals(1)
        self.ffund_spin.setValue(50.0)
        self.ffund_btn = QPushButton("Set FFUND")
        self.ffund_btn.clicked.connect(self._send_ffund)
        ffund_row.addWidget(QLabel("Fund (Hz)"))
        ffund_row.addWidget(self.ffund_spin, 1)
        ffund_row.addWidget(self.ffund_btn)
        layout.addLayout(ffund_row)

        vnom_row = QHBoxLayout()
        self.vnom_spin = QDoubleSpinBox()
        self.vnom_spin.setRange(5.0, 60.0)
        self.vnom_spin.setSingleStep(1.0)
        self.vnom_spin.setDecimals(1)
        self.vnom_spin.setValue(50.0)
        self.vnom_btn = QPushButton("Set VNOM")
        self.vnom_btn.clicked.connect(self._send_vnom)
        vnom_row.addWidget(QLabel("Bus Vnom (V)"))
        vnom_row.addWidget(self.vnom_spin, 1)
        vnom_row.addWidget(self.vnom_btn)
        layout.addLayout(vnom_row)

        oc_row = QHBoxLayout()
        self.oc_spin = QDoubleSpinBox()
        self.oc_spin.setRange(0.5, 20.0)
        self.oc_spin.setSingleStep(0.5)
        self.oc_spin.setDecimals(1)
        self.oc_spin.setValue(15.0)
        self.oc_btn = QPushButton("Set OC")
        self.oc_btn.clicked.connect(self._send_oc)
        oc_row.addWidget(QLabel("Overcurrent (A)"))
        oc_row.addWidget(self.oc_spin, 1)
        oc_row.addWidget(self.oc_btn)
        layout.addLayout(oc_row)

        return group

    def _send_mod(self) -> None:
        self._send_command(f"MOD {self.mod_combo.currentText().strip().upper()}")

    def _send_vnom(self) -> None:
        self._send_command(f"VNOM {self.vnom_spin.value():.2f}")

    def _send_oc(self) -> None:
        self._send_command(f"OC {self.oc_spin.value():.2f}")

    def _send_fsw(self) -> None:
        text = self.fsw_combo.currentText().strip()
        try:
            hz = int(float(text))
        except ValueError:
            self._log_event("ERROR", f"Invalid FSW value: {text}")
            return
        self._send_command(f"FSW {hz}")

    def _send_bridge(self) -> None:
        self._send_command(f"BRIDGE {self.bridge_combo.currentText().strip().upper()}")

    def _send_ffund(self) -> None:
        self._send_command(f"FFUND {self.ffund_spin.value():.2f}")

    def _make_scenario_group(self) -> QGroupBox:
        group = QGroupBox("PC-only Fault Scenarios")
        grid = QGridLayout(group)
        self.scenario_buttons: list[QPushButton] = []
        for index, scenario in enumerate(SCENARIOS.values()):
            button = QPushButton(scenario.label)
            button.setToolTip(scenario.description)
            button.clicked.connect(lambda checked=False, key=scenario.key: self._run_scenario(key))
            row = index // 2
            col = index % 2
            grid.addWidget(button, row, col)
            self.scenario_buttons.append(button)
        return group

    def _connect_sources(self) -> None:
        for source in (self.sim_source, self.serial_source):
            source.frame_received.connect(self._handle_frame)
            source.event_received.connect(self._log_event)
            source.connection_changed.connect(self._set_connection_text)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background:#0d0f10; color:#e1e3df; font-family: Segoe UI; font-size: 10pt; }
            QFrame#topBar, QGroupBox { background:#17191b; border:1px solid #303436; border-radius:4px; }
            QGroupBox { margin-top: 15px; padding-top: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color:#c8cbc7; }
            QPushButton, QComboBox, QDoubleSpinBox {
                background:#202326; border:1px solid #3b3f42; border-radius:3px; padding:4px 6px;
            }
            QPushButton:hover { border-color:#7aa89f; }
            QPushButton:disabled { color:#646967; border-color:#25282a; background:#151719; }
            QCheckBox { spacing:8px; }
            QTextEdit { background:#0a0b0c; border:1px solid #303436; border-radius:3px; color:#c8cbc7; }
            QTabWidget::pane { border:1px solid #303436; background:#17191b; top:-1px; }
            QTabBar::tab {
                background:#202326; border:1px solid #303436; padding:6px 14px;
                margin-right:2px; border-top-left-radius:3px; border-top-right-radius:3px;
            }
            QTabBar::tab:selected { background:#17191b; border-bottom-color:#17191b; color:#e1e3df; }
            QLabel#safetyBox {
                background:#211f18; border:1px solid #5b5135; border-radius:3px;
                padding:10px; color:#d3c28b;
            }
            """
        )

    def _set_source(self, name: str) -> None:
        self.current_source_name = name
        live = name == "Live serial"
        self.port_combo.setEnabled(live)
        self.refresh_ports_btn.setEnabled(live)
        self.connect_btn.setEnabled(live)
        self.arm_live.setEnabled(live)
        if not live:
            self.arm_live.setChecked(False)
            self.sim_source.start()
            self._set_connection_text("Simulator running")
        else:
            self.sim_source.stop()
            self.pwm_twin.set_running(False)
            self.modulation_widget.set_running(False)
            self._set_connection_text("Live serial selected")
        self._update_scenario_buttons()

    def _refresh_ports(self) -> None:
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = SerialSource.available_ports()
        if ports:
            self.port_combo.addItems(ports)
            if current in ports:
                self.port_combo.setCurrentText(current)
        else:
            self.port_combo.addItem("No ports")

    def _toggle_serial(self) -> None:
        if self.serial_source.port is not None:
            self.serial_source.disconnect_port()
            self.connect_btn.setText("Connect")
            return
        port = self.port_combo.currentText()
        if not port or port == "No ports":
            self._log_event("ERROR", "No serial port selected")
            return
        if self.serial_source.connect_port(port):
            self.connect_btn.setText("Disconnect")

    def _active_source(self):
        return self.serial_source if self.current_source_name == "Live serial" else self.sim_source

    def _send_start(self) -> None:
        if self.current_source_name == "Live serial" and not self.arm_live.isChecked():
            self._log_event("SAFETY", "START blocked until 'Arm live START' is checked")
            return
        self._send_command("START")

    def _send_mode(self) -> None:
        mode = self.mode_combo.currentData()
        self._send_command(f"MODE {MODE_IDS[mode]}")

    def _send_command(self, command: str) -> None:
        text = command.strip().upper()
        if text.startswith("MI "):
            try:
                self.current_modulation_index = max(0.0, min(0.95, float(text.split()[1])))
            except (IndexError, ValueError):
                pass
        self._active_source().send_command(command)

    def _run_scenario(self, key: str) -> None:
        if self.current_source_name == "Live serial":
            self.source_combo.setCurrentText("Simulator")
            self._log_event("SAFETY", "Switched to simulator for PC-only scenario playback")
        self._clear_history()
        self.sim_source.play_scenario(key)
        self._update_scenario_buttons()

    def _normalize_sim(self) -> None:
        self.sim_source.normalize()
        if self.current_source_name != "Live serial":
            self.sim_source.send_command("CLEAR")

    def _update_scenario_buttons(self) -> None:
        live_armed = self.current_source_name == "Live serial" and self.arm_live.isChecked()
        for button in getattr(self, "scenario_buttons", []):
            button.setEnabled(not live_armed)

    def _handle_frame(self, frame: TelemetryFrame) -> None:
        if self.current_source_name == "Live serial" and frame.source != "serial":
            return
        if self.current_source_name != "Live serial" and frame.source == "serial":
            return
        if frame.source == "serial":
            frame = replace(frame, modulation_index=self.current_modulation_index)
        else:
            self.current_modulation_index = frame.modulation_index
        self.last_frame = frame
        self.state_label.setText(f"State: {frame.state}")
        self.mode_label.setText(f"Mode: {frame.mode}")
        self.fault_badge.set_faults(frame.fault_bits, frame.fault_text)
        self.fsm_widget.set_state(frame.state)
        self.modulation_widget.set_frame(frame)
        self.pwm_twin.set_frame(frame)
        self.vdc1_gauge.set_value(frame.vdc1)
        self.vdc2_gauge.set_value(frame.vdc2)
        self.iout_gauge.set_value(frame.iout)
        self.imbalance_gauge.set_value(frame.imbalance)
        self._append_history(frame)
        self._update_plot()
        if frame.open_loop:
            self.safety_box.setText("OPEN mode: no active firmware protection. Use only for low-risk demos.")
        else:
            self.safety_box.setText("PC-only simulation: scenarios never write fake faults to firmware.")

    def _append_history(self, frame: TelemetryFrame) -> None:
        self.t_history.append(frame.ms / 1000.0)
        self.vdc1_history.append(math.nan if frame.vdc1 is None else frame.vdc1)
        self.vdc2_history.append(math.nan if frame.vdc2 is None else frame.vdc2)
        self.iout_history.append(math.nan if frame.iout is None else frame.iout)
        for series in (
            self.t_history,
            self.vdc1_history,
            self.vdc2_history,
            self.iout_history,
        ):
            if len(series) > self.history_limit:
                del series[: len(series) - self.history_limit]

    def _update_plot(self) -> None:
        self.vdc1_curve.setData(self.t_history, self.vdc1_history)
        self.vdc2_curve.setData(self.t_history, self.vdc2_history)
        self.iout_curve.setData(self.t_history, self.iout_history)
        if self.follow_plot.isChecked() and self.t_history:
            right = max(self.plot_window_seconds, self.t_history[-1])
            left = right - self.plot_window_seconds
            self.plot.setXRange(left, right, padding=0)

    def _clear_history(self) -> None:
        self.t_history.clear()
        self.vdc1_history.clear()
        self.vdc2_history.clear()
        self.iout_history.clear()
        self._update_plot()
        self.plot.setXRange(0.0, self.plot_window_seconds, padding=0)

    def _log_event(self, channel: str, message: str) -> None:
        if channel == "STATUS":
            self._consume_status_message(message)
        self.log.append(f"[{channel}] {message}")

    def _set_connection_text(self, text: str) -> None:
        self.connection_label.setText(text)
        if "stopped" in text.lower() or "disconnected" in text.lower():
            self.pwm_twin.set_running(False)
            self.modulation_widget.set_running(False)

    def _animate_visuals(self) -> None:
        self.modulation_widget.animate()
        self.pwm_twin.animate()

    def _plot_manually_changed(self, *args) -> None:
        del args
        self.follow_plot.setChecked(False)

    def _set_plot_window(self, value: float) -> None:
        self.plot_window_seconds = float(value)
        if self.follow_plot.isChecked():
            self._update_plot()

    def _zoom_plot(self, factor: float) -> None:
        new_window = max(2.0, min(120.0, self.plot_window_seconds * factor))
        self.window_spin.blockSignals(True)
        self.window_spin.setValue(new_window)
        self.window_spin.blockSignals(False)
        self.plot_window_seconds = new_window
        if self.follow_plot.isChecked():
            self._update_plot()
            return
        x_range, _ = self.plot.getViewBox().viewRange()
        center = (x_range[0] + x_range[1]) / 2.0
        self.plot.setXRange(center - new_window / 2.0, center + new_window / 2.0, padding=0)

    def _reset_plot_view(self) -> None:
        self.plot_window_seconds = 12.0
        self.window_spin.blockSignals(True)
        self.window_spin.setValue(self.plot_window_seconds)
        self.window_spin.blockSignals(False)
        self.follow_plot.setChecked(True)
        self.plot.setYRange(-22.0, 70.0, padding=0.02)
        self._update_plot()

    def _consume_status_message(self, message: str) -> None:
        fields = {}
        for item in message.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        if "mi" not in fields:
            return
        try:
            self.current_modulation_index = max(0.0, min(0.95, float(fields["mi"])))
            self.mi_spin.setValue(self.current_modulation_index)
        except ValueError:
            return

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override.
        self.sim_source.stop()
        self.serial_source.disconnect_port()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("5-Level CHB Visual Twin Dashboard")
    try:
        window = DashboardWindow()
    except RuntimeError as exc:
        QMessageBox.critical(None, "Dashboard dependency missing", str(exc))
        return 2

    quit_action = QAction("Quit", window)
    quit_action.setShortcut("Ctrl+Q")
    quit_action.triggered.connect(app.quit)
    window.addAction(quit_action)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
