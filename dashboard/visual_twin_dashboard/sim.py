from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional

from .models import (
    FAULT_IMBAL,
    FAULT_NONE,
    FAULT_OC,
    FAULT_OV,
    FAULT_SENSOR_LOST,
    FAULT_UV,
    MODE_IDS,
    MODE_NAMES,
    PROTECTION_IMBALANCE_V,
    PROTECTION_OVERCURRENT_A,
    PROTECTION_OVERVOLTAGE_V,
    PROTECTION_UNDERVOLTAGE_V,
    TelemetryFrame,
)


VISUAL_PRECHARGE_MS = 350
SCENARIO_TRIP_MS = 1200


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    description: str


SCENARIOS: Dict[str, Scenario] = {
    "nominal": Scenario("nominal", "Nominal run", "Balanced DC buses and modest output current."),
    "undervoltage": Scenario("undervoltage", "Undervoltage", "DC bus drops below 40 V."),
    "overvoltage": Scenario("overvoltage", "Overvoltage", "DC bus rises above 58 V."),
    "overcurrent": Scenario("overcurrent", "Overcurrent", "Output current exceeds 15 A."),
    "imbalance": Scenario("imbalance", "DC imbalance", "DC buses differ by more than 10 V."),
    "sensor_lost": Scenario("sensor_lost", "Sensor lost", "Required sensor goes unavailable."),
    "open_loop": Scenario("open_loop", "Open loop", "No sensors and no active protection."),
    "mode_demotion": Scenario("mode_demotion", "Mode demotion", "Boot selects a reduced sensing mode."),
}


class SimController:
    def __init__(self) -> None:
        self.ms = 0
        self.state = "IDLE"
        self.mode = "FULL"
        self.fault_bits = FAULT_NONE
        self.modulation_index = 0.95
        self.scenario_key = "nominal"
        self.scenario_started_ms = 0
        self.precharge_until_ms: Optional[int] = None
        self.phase = 0.42
        self.event: Optional[str] = None

    def start(self) -> str:
        if self.state != "IDLE":
            return "START_ALLOWED_ONLY_IN_IDLE"
        self.fault_bits = FAULT_NONE
        self.state = "PRECHARGE"
        self.precharge_until_ms = self.ms + VISUAL_PRECHARGE_MS
        return "START"

    def stop(self) -> str:
        if self.state not in ("PRECHARGE", "RUN"):
            return "STOP_ALLOWED_ONLY_WHILE_RUNNING"
        self.state = "IDLE"
        self.precharge_until_ms = None
        return "STOP"

    def clear(self) -> str:
        if self.state != "FAULT":
            return "CLEAR_ALLOWED_ONLY_IN_FAULT"
        if self.active_faults() != FAULT_NONE:
            return "FAULT_STILL_ACTIVE"
        self.fault_bits = FAULT_NONE
        self.state = "IDLE"
        return "CLEAR"

    def set_mode(self, mode: str) -> str:
        if self.state not in ("IDLE", "FAULT"):
            return "MODE_CHANGE_REQUIRES_STOP"
        if mode not in MODE_IDS:
            return "MODE_SENSOR_UNAVAILABLE"
        self.mode = mode
        return f"MODE {MODE_IDS[mode]}"

    def set_modulation_index(self, value: float) -> str:
        if self.state != "IDLE":
            return "MI_ALLOWED_ONLY_IN_IDLE"
        if value < 0.0 or value > 0.95:
            return "MI_RANGE_0_TO_0_95"
        self.modulation_index = value
        return f"MI {value:.2f}"

    def run_scenario(self, key: str) -> str:
        if key not in SCENARIOS:
            raise KeyError(key)
        self.scenario_key = key
        self.scenario_started_ms = self.ms
        self.fault_bits = FAULT_NONE
        self.precharge_until_ms = None
        self.event = None

        if key == "mode_demotion":
            self.state = "BOOT"
            self.mode = "DC1"
            self.event = "MODE_DEMOTED"
            return "BOOT_SELF_TEST_DONE"
        if key == "open_loop":
            self.state = "IDLE"
            self.mode = "OPEN"
            self.event = "WARNING_OPEN_LOOP_NO_PROTECTION"
            self.start()
            return "WARNING_OPEN_LOOP_NO_PROTECTION"

        self.state = "IDLE"
        self.mode = "FULL"
        self.start()
        return SCENARIOS[key].label

    def normalize_fault_condition(self) -> None:
        self.scenario_key = "nominal"
        self.scenario_started_ms = self.ms

    def step(self, dt_ms: int = 50) -> TelemetryFrame:
        self.ms += max(1, int(dt_ms))
        self.phase = (self.phase + (2.0 * math.pi * 50.0 * dt_ms / 1000.0)) % (2.0 * math.pi)

        if self.state == "BOOT" and self.ms - self.scenario_started_ms >= 700:
            self.state = "IDLE"
        if self.state == "PRECHARGE" and self.precharge_until_ms is not None:
            if self.ms >= self.precharge_until_ms:
                self.state = "RUN"
                self.precharge_until_ms = None

        faults = self.active_faults()
        if self.state in ("PRECHARGE", "RUN") and faults != FAULT_NONE:
            self.fault_bits |= faults
            self.state = "FAULT"

        vdc1, vdc2, iout = self.sensor_values()
        return TelemetryFrame(
            ms=self.ms,
            state=self.state,
            mode=self.mode,
            fault_bits=self.fault_bits,
            vdc1=vdc1,
            vdc2=vdc2,
            iout=iout,
            level=self.output_level(),
            checksum_valid=True,
            source="sim",
            modulation_index=self.modulation_index,
        )

    def sensor_values(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        elapsed = self.ms - self.scenario_started_ms
        ripple = math.sin(self.ms / 450.0) * 0.24
        current = math.sin(self.ms / 180.0) * 3.2
        vdc1: Optional[float] = 50.0 + ripple
        vdc2: Optional[float] = 50.2 - ripple
        iout: Optional[float] = current

        if self.scenario_key == "undervoltage" and elapsed >= SCENARIO_TRIP_MS:
            vdc1 = 37.5
            vdc2 = 38.2
        elif self.scenario_key == "overvoltage" and elapsed >= SCENARIO_TRIP_MS:
            vdc1 = 60.8
            vdc2 = 60.1
        elif self.scenario_key == "overcurrent" and elapsed >= SCENARIO_TRIP_MS:
            iout = 18.6 * (1.0 if math.sin(self.ms / 130.0) >= 0.0 else -1.0)
        elif self.scenario_key == "imbalance" and elapsed >= SCENARIO_TRIP_MS:
            vdc1 = 56.0
            vdc2 = 44.4
        elif self.scenario_key == "sensor_lost" and elapsed >= SCENARIO_TRIP_MS:
            vdc2 = None
        elif self.scenario_key == "open_loop":
            vdc1 = None
            vdc2 = None
            iout = None
        elif self.scenario_key == "mode_demotion":
            vdc1 = 50.0 + ripple
            vdc2 = None
            iout = None

        if self.mode == "OPEN":
            return None, None, None
        if self.mode == "DC_ONLY":
            return vdc1, vdc2, None
        if self.mode == "CUR_ONLY":
            return None, None, iout
        if self.mode == "DC1":
            return vdc1, None, iout
        if self.mode == "DC2":
            return None, vdc2, iout
        return vdc1, vdc2, iout

    def active_faults(self) -> int:
        if self.mode == "OPEN":
            return FAULT_NONE

        vdc1, vdc2, iout = self.sensor_values()
        faults = FAULT_NONE

        if self.scenario_key == "sensor_lost" and self.ms - self.scenario_started_ms >= SCENARIO_TRIP_MS:
            return FAULT_SENSOR_LOST

        def check_dc(value: Optional[float]) -> int:
            if value is None:
                return FAULT_NONE
            result = FAULT_NONE
            if value < PROTECTION_UNDERVOLTAGE_V:
                result |= FAULT_UV
            if value > PROTECTION_OVERVOLTAGE_V:
                result |= FAULT_OV
            return result

        if self.mode in ("FULL", "DC_ONLY", "DC1"):
            faults |= check_dc(vdc1)
        if self.mode in ("FULL", "DC_ONLY", "DC2"):
            faults |= check_dc(vdc2)
        if iout is not None and self.mode in ("FULL", "CUR_ONLY", "DC1", "DC2"):
            if abs(iout) > PROTECTION_OVERCURRENT_A:
                faults |= FAULT_OC
        if self.mode in ("FULL", "DC_ONLY") and vdc1 is not None and vdc2 is not None:
            if abs(vdc1 - vdc2) > PROTECTION_IMBALANCE_V:
                faults |= FAULT_IMBAL
        return faults

    def output_level(self) -> int:
        if self.state not in ("PRECHARGE", "RUN"):
            return 0
        ref = self.modulation_index * math.sin(self.phase)
        if ref >= 0.6:
            return 2
        if ref >= 0.2:
            return 1
        if ref <= -0.6:
            return -2
        if ref <= -0.2:
            return -1
        return 0


def mode_name_from_id(mode_id: int) -> str:
    return MODE_NAMES[mode_id]
