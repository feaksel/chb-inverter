from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


STATE_NAMES = ("BOOT", "IDLE", "PRECHARGE", "RUN", "FAULT")
MODE_NAMES = ("FULL", "DC_ONLY", "CUR_ONLY", "OPEN", "DC1", "DC2")

MODE_IDS: Dict[str, int] = {name: index for index, name in enumerate(MODE_NAMES)}
MODE_LABELS: Dict[str, str] = {
    "FULL": "Full sensing",
    "DC_ONLY": "DC buses",
    "CUR_ONLY": "Current only",
    "OPEN": "Open loop",
    "DC1": "DC1 only",
    "DC2": "DC2 only",
}

FAULT_NONE = 0x00
FAULT_UV = 0x01
FAULT_OV = 0x02
FAULT_OC = 0x04
FAULT_IMBAL = 0x08
FAULT_SENSOR_LOST = 0x10
FAULT_MANUAL = 0x20

FAULT_NAMES: Dict[int, str] = {
    FAULT_UV: "UV",
    FAULT_OV: "OV",
    FAULT_OC: "OC",
    FAULT_IMBAL: "IMBAL",
    FAULT_SENSOR_LOST: "SENSOR_LOST",
    FAULT_MANUAL: "MANUAL",
}

PROTECTION_UNDERVOLTAGE_V = 40.0
PROTECTION_OVERVOLTAGE_V = 58.0
PROTECTION_OVERCURRENT_A = 15.0
PROTECTION_IMBALANCE_V = 10.0


@dataclass(frozen=True)
class TelemetryFrame:
    ms: int
    state: str
    mode: str
    fault_bits: int
    vdc1: Optional[float]
    vdc2: Optional[float]
    iout: Optional[float]
    level: int
    checksum_valid: bool = True
    source: str = "sim"
    modulation_index: float = 0.95

    @property
    def fault_text(self) -> str:
        return fault_text(self.fault_bits)

    @property
    def imbalance(self) -> Optional[float]:
        if self.vdc1 is None or self.vdc2 is None:
            return None
        return abs(self.vdc1 - self.vdc2)

    @property
    def open_loop(self) -> bool:
        return self.mode == "OPEN"


def fault_text(bits: int) -> str:
    names = [name for bit, name in FAULT_NAMES.items() if bits & bit]
    return "|".join(names) if names else "NONE"


def bridge_states_for_level(level: int) -> Tuple[int, int]:
    if level >= 2:
        return 1, 1
    if level == 1:
        return 1, 0
    if level == 0:
        return 0, 0
    if level == -1:
        return -1, 0
    return -1, -1


def mode_uses_sensor(mode: str, sensor: str, current_available: bool = True) -> bool:
    if sensor == "vdc1":
        return mode in ("FULL", "DC_ONLY", "DC1")
    if sensor == "vdc2":
        return mode in ("FULL", "DC_ONLY", "DC2")
    if sensor == "iout":
        return mode in ("FULL", "CUR_ONLY") or (
            mode in ("DC1", "DC2") and current_available
        )
    return False
