from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from visual_twin_dashboard.models import (  # noqa: E402
    FAULT_IMBAL,
    FAULT_NONE,
    FAULT_OC,
    FAULT_OV,
    FAULT_SENSOR_LOST,
    FAULT_UV,
)
from visual_twin_dashboard.sim import SCENARIO_TRIP_MS, VISUAL_PRECHARGE_MS, SimController  # noqa: E402


class SimulatorTests(unittest.TestCase):
    def test_start_precharge_run_transition(self) -> None:
        sim = SimController()

        self.assertEqual(sim.start(), "START")
        precharge = sim.step(50)
        self.assertEqual(precharge.state, "PRECHARGE")

        run = sim.step(VISUAL_PRECHARGE_MS)
        self.assertEqual(run.state, "RUN")
        self.assertEqual(run.fault_bits, FAULT_NONE)

    def test_undervoltage_latches_fault(self) -> None:
        sim = SimController()
        sim.run_scenario("undervoltage")

        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(frame.state, "FAULT")
        self.assertTrue(frame.fault_bits & FAULT_UV)

    def test_overvoltage_latches_fault(self) -> None:
        sim = SimController()
        sim.run_scenario("overvoltage")

        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(frame.state, "FAULT")
        self.assertTrue(frame.fault_bits & FAULT_OV)

    def test_overcurrent_latches_fault(self) -> None:
        sim = SimController()
        sim.run_scenario("overcurrent")

        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(frame.state, "FAULT")
        self.assertTrue(frame.fault_bits & FAULT_OC)

    def test_imbalance_latches_fault_without_uv_or_ov(self) -> None:
        sim = SimController()
        sim.run_scenario("imbalance")

        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(frame.state, "FAULT")
        self.assertTrue(frame.fault_bits & FAULT_IMBAL)
        self.assertFalse(frame.fault_bits & FAULT_UV)
        self.assertFalse(frame.fault_bits & FAULT_OV)

    def test_sensor_lost_latches_fault(self) -> None:
        sim = SimController()
        sim.run_scenario("sensor_lost")

        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(frame.state, "FAULT")
        self.assertTrue(frame.fault_bits & FAULT_SENSOR_LOST)
        self.assertIsNone(frame.vdc2)

    def test_clear_requires_fault_condition_to_be_normal(self) -> None:
        sim = SimController()
        sim.run_scenario("undervoltage")
        sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(sim.clear(), "FAULT_STILL_ACTIVE")
        sim.normalize_fault_condition()
        sim.step(50)

        self.assertEqual(sim.clear(), "CLEAR")
        self.assertEqual(sim.state, "IDLE")
        self.assertEqual(sim.fault_bits, FAULT_NONE)

    def test_open_loop_has_no_faults_and_no_sensor_values(self) -> None:
        sim = SimController()
        sim.run_scenario("open_loop")

        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)

        self.assertEqual(frame.mode, "OPEN")
        self.assertEqual(frame.fault_bits, FAULT_NONE)
        self.assertIsNone(frame.vdc1)
        self.assertIsNone(frame.vdc2)
        self.assertIsNone(frame.iout)

    def test_mode_demotion_boots_to_reduced_mode(self) -> None:
        sim = SimController()
        sim.run_scenario("mode_demotion")

        boot = sim.step(50)
        idle = sim.step(700)

        self.assertEqual(boot.state, "BOOT")
        self.assertEqual(idle.state, "IDLE")
        self.assertEqual(idle.mode, "DC1")
        self.assertIsNone(idle.vdc2)


if __name__ == "__main__":
    unittest.main()

