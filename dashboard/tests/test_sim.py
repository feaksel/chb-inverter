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

    def test_pwm_config_defaults_and_setters(self) -> None:
        sim = SimController()
        self.assertEqual(sim.modulator, "STAIR")
        self.assertEqual(sim.switching_freq_hz, 500)
        self.assertEqual(sim.bridge_select, "BOTH")
        self.assertAlmostEqual(sim.fundamental_freq_hz, 50.0)

        self.assertEqual(sim.set_modulator("PSC"), "MOD PSC")
        self.assertEqual(sim.modulator, "PSC")
        self.assertEqual(sim.set_bridge("B1"), "BRIDGE B1")
        self.assertEqual(sim.bridge_select, "B1")
        self.assertEqual(sim.set_switching_freq(5000), "FSW 5000")
        self.assertEqual(sim.switching_freq_hz, 5000)
        self.assertEqual(sim.set_fundamental_freq(60.0), "FFUND 60.00")
        self.assertAlmostEqual(sim.fundamental_freq_hz, 60.0)

    def test_stair_alt_modulator_accepted(self) -> None:
        sim = SimController()
        self.assertEqual(sim.set_modulator("STAIR_ALT"), "MOD STAIR_ALT")
        self.assertEqual(sim.modulator, "STAIR_ALT")
        # And we can flip back:
        self.assertEqual(sim.set_modulator("STAIR"), "MOD STAIR")
        self.assertEqual(sim.modulator, "STAIR")

    def test_protection_config_defaults_and_derived_thresholds(self) -> None:
        sim = SimController()
        self.assertAlmostEqual(sim.nominal_voltage, 50.0)
        self.assertAlmostEqual(sim.overcurrent_a, 15.0)
        # At VNOM=50 the derived thresholds reproduce the original fixed design.
        self.assertAlmostEqual(sim.undervoltage_threshold(), 40.0)
        self.assertAlmostEqual(sim.overvoltage_threshold(), 58.0)
        self.assertAlmostEqual(sim.imbalance_threshold(), 10.0)

    def test_set_nominal_voltage_scales_thresholds(self) -> None:
        sim = SimController()
        self.assertEqual(sim.set_nominal_voltage(12.0), "VNOM 12.00")
        self.assertAlmostEqual(sim.nominal_voltage, 12.0)
        self.assertAlmostEqual(sim.undervoltage_threshold(), 9.6)
        self.assertAlmostEqual(sim.overvoltage_threshold(), 13.92)
        self.assertAlmostEqual(sim.imbalance_threshold(), 2.4)

    def test_protection_config_range_rejection(self) -> None:
        sim = SimController()
        self.assertEqual(sim.set_nominal_voltage(3.0), "VNOM_RANGE_5_TO_60")
        self.assertEqual(sim.set_nominal_voltage(80.0), "VNOM_RANGE_5_TO_60")
        self.assertEqual(sim.set_overcurrent(0.1), "OC_RANGE_0_5_TO_20")
        self.assertEqual(sim.set_overcurrent(25.0), "OC_RANGE_0_5_TO_20")
        # Rejected values leave the defaults intact.
        self.assertAlmostEqual(sim.nominal_voltage, 50.0)
        self.assertAlmostEqual(sim.overcurrent_a, 15.0)

    def test_low_voltage_run_does_not_trip_after_vnom_set(self) -> None:
        # The whole point of VNOM: a 12 V bench test must not trip UV.
        sim = SimController()
        self.assertEqual(sim.set_nominal_voltage(12.0), "VNOM 12.00")
        self.assertEqual(sim.start(), "START")
        frame = sim.step(SCENARIO_TRIP_MS + VISUAL_PRECHARGE_MS)
        self.assertEqual(frame.state, "RUN")
        self.assertEqual(frame.fault_bits, FAULT_NONE)
        # And the sensor model now reports ~12 V, not ~50 V.
        self.assertIsNotNone(frame.vdc1)
        self.assertLess(abs(frame.vdc1 - 12.0), 1.0)

    def test_protection_config_requires_idle_or_fault(self) -> None:
        sim = SimController()
        sim.start()
        sim.step(VISUAL_PRECHARGE_MS + 50)  # now in RUN
        self.assertEqual(sim.state, "RUN")
        self.assertEqual(sim.set_nominal_voltage(12.0),
                         "PROTECTION_CONFIG_REQUIRES_IDLE_OR_FAULT")
        self.assertEqual(sim.set_overcurrent(10.0),
                         "PROTECTION_CONFIG_REQUIRES_IDLE_OR_FAULT")

    def test_pwm_config_rejects_out_of_range(self) -> None:
        sim = SimController()
        self.assertEqual(sim.set_modulator("BOGUS"), "PWM_CONFIG_REJECTED")
        self.assertEqual(sim.set_bridge("X"), "PWM_CONFIG_REJECTED")
        self.assertEqual(sim.set_switching_freq(50), "FSW_RANGE_100_TO_20000")
        self.assertEqual(sim.set_switching_freq(30000), "FSW_RANGE_100_TO_20000")
        self.assertEqual(sim.set_fundamental_freq(5.0), "FFUND_RANGE_10_TO_400")

    def test_pwm_config_requires_idle(self) -> None:
        sim = SimController()
        sim.start()
        sim.step(50)
        self.assertEqual(sim.state, "PRECHARGE")
        self.assertEqual(sim.set_modulator("PSC"), "PWM_CONFIG_REQUIRES_IDLE")
        self.assertEqual(sim.set_switching_freq(5000), "PWM_CONFIG_REQUIRES_IDLE")
        self.assertEqual(sim.set_bridge("B1"), "PWM_CONFIG_REQUIRES_IDLE")
        self.assertEqual(sim.set_fundamental_freq(60.0), "PWM_CONFIG_REQUIRES_IDLE")

    def test_config_summary_format(self) -> None:
        sim = SimController()
        sim.set_modulator("PSC")
        sim.set_switching_freq(5000)
        sim.set_bridge("B2")
        sim.set_fundamental_freq(60.0)
        self.assertEqual(
            sim.config_summary(),
            "mod=PSC,fsw=5000,bridge=B2,ffund=60.00,mi=0.95",
        )


if __name__ == "__main__":
    unittest.main()

