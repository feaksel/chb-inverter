from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from visual_twin_dashboard.models import (  # noqa: E402
    FAULT_IMBAL,
    FAULT_SENSOR_LOST,
    FAULT_UV,
    MODE_NAMES,
    STATE_NAMES,
    TelemetryFrame,
    fault_text,
)
from visual_twin_dashboard.protocol import make_telemetry_line, parse_line, parse_telemetry  # noqa: E402


class ProtocolTests(unittest.TestCase):
    def test_valid_telemetry_checksum(self) -> None:
        frame = TelemetryFrame(12345, "RUN", "FULL", 0x00, 49.87, 50.02, 3.41, 1)
        line = make_telemetry_line(frame)
        parsed = parse_telemetry(line, source="serial")

        self.assertTrue(parsed.checksum_valid)
        self.assertEqual(parsed.ms, 12345)
        self.assertEqual(parsed.state, "RUN")
        self.assertEqual(parsed.mode, "FULL")
        self.assertAlmostEqual(parsed.vdc1 or 0.0, 49.87)
        self.assertEqual(parsed.level, 1)

    def test_bad_checksum_still_returns_frame_marked_invalid(self) -> None:
        frame = TelemetryFrame(100, "RUN", "FULL", 0x00, 50.0, 50.0, 1.0, -1)
        line = make_telemetry_line(frame)
        bad_line = line[:-2] + "00"

        parsed = parse_telemetry(bad_line)

        self.assertFalse(parsed.checksum_valid)
        self.assertEqual(parsed.level, -1)

    def test_nan_sensor_values(self) -> None:
        line = "$T,150,IDLE,OPEN,0x00,NAN,NAN,NAN,0*00"
        parsed = parse_telemetry(line)

        self.assertIsNone(parsed.vdc1)
        self.assertIsNone(parsed.vdc2)
        self.assertIsNone(parsed.iout)
        self.assertFalse(parsed.checksum_valid)

    def test_all_states_and_modes_parse(self) -> None:
        for state in STATE_NAMES:
            for mode in MODE_NAMES:
                frame = TelemetryFrame(1, state, mode, 0, None, None, None, 0)
                parsed = parse_telemetry(make_telemetry_line(frame))
                self.assertEqual(parsed.state, state)
                self.assertEqual(parsed.mode, mode)

    def test_combined_fault_mask_text(self) -> None:
        bits = FAULT_UV | FAULT_IMBAL | FAULT_SENSOR_LOST
        frame = TelemetryFrame(500, "FAULT", "FULL", bits, 36.0, 50.0, 0.0, 0)
        parsed = parse_telemetry(make_telemetry_line(frame))

        self.assertEqual(parsed.fault_bits, bits)
        self.assertEqual(fault_text(parsed.fault_bits), "UV|IMBAL|SENSOR_LOST")

    def test_parse_status_ack_error_fault_and_help_lines(self) -> None:
        status = parse_line("$S,ms=1,state=IDLE,mode=FULL,fault=0x00,avail=0x07")
        ack = parse_line("$A,START")
        error = parse_line("$E,MODE_SENSOR_UNAVAILABLE")
        fault = parse_line("$F,0x09,UV|IMBAL")
        help_line = parse_line("$H,START STOP CLEAR MODE 0..5 STATUS HELP MI 0.0..0.95")

        self.assertEqual(status.kind, "status")
        self.assertEqual(status.fields["state"], "IDLE")
        self.assertEqual(ack.kind, "ack")
        self.assertEqual(error.kind, "error")
        self.assertEqual(fault.kind, "fault")
        self.assertEqual(help_line.kind, "help")


if __name__ == "__main__":
    unittest.main()

