"""Test procedure TC-1..TC-3 for the 2U UHF antenna deployment (run against the virtual-time model)."""
import unittest

from uhf_antenna_deployment_sim import Antenna, AntennaMCU, Clock, UHFTransceiver


def build(faulty=(), gpo_fault=False, mcu_healthy=True):
    clock = Clock()
    antenna = Antenna(clock, faulty_resistors=faulty, gpo_fault=gpo_fault)
    mcu = AntennaMCU(antenna, healthy=mcu_healthy)
    uhf = UHFTransceiver(antenna, mcu)
    return antenna, mcu, uhf


class TC1_NominalMcuDeployment(unittest.TestCase):
    def test_nominal_first_boot(self):
        antenna, mcu, uhf = build()
        mcu.run()

        # Burn sequence timing (boot + 120 s delay)
        for r in ("A1", "A2"):
            self.assertEqual(antenna.event_times(r, "ON"), [120])
            self.assertEqual(antenna.event_times(r, "OFF"), [130])
        for r in ("B1", "B2"):
            self.assertEqual(antenna.event_times(r, "ON"), [125])
            self.assertEqual(antenna.event_times(r, "OFF"), [135])

        # Flag cleared, antenna deployed, no second MCU attempt
        self.assertEqual(mcu.robust_flag, 0)
        self.assertEqual(antenna.released_rods, [1, 2, 3, 4])
        self.assertEqual(len(antenna.runs), 1)

        # UHF wakes at 300 s, sees "deployed", starts nothing
        uhf.run()
        self.assertEqual(len(antenna.runs), 1)


class TC2_BurnResistorRedundancy(unittest.TestCase):
    def test_single_pair_or_resistor_failure_still_deploys(self):
        cases = {
            "pair A failed": ({"A1", "A2"}, ("B1", "B2")),
            "pair B failed": ({"B1", "B2"}, ("A1", "A2")),
            "A1 failed": ({"A1"}, ("B1", "A2")),
            "B2 failed": ({"B2"}, ("A1", "B1")),
        }
        for name, (faulty, healthy_that_must_burn) in cases.items():
            with self.subTest(name):
                antenna, mcu, _ = build(faulty=faulty)
                mcu.run()
                for r in healthy_that_must_burn:
                    self.assertEqual(antenna.on_time_of(r), 10)
                self.assertEqual(antenna.released_rods, [1, 2, 3, 4])
                self.assertEqual(len(antenna.runs), 1)

    def test_both_resistors_of_one_wire_failed_is_detected(self):
        # Negative control: no redundancy left for wire 1, so the check must fail.
        antenna, mcu, _ = build(faulty={"A1", "B1"})
        mcu.run()
        self.assertEqual(antenna.released_rods, [3, 4])
        self.assertFalse(antenna.deployed)
        self.assertEqual(len(antenna.runs), 2)  # MCU retried once


class TC3_UhfFallbackWhenMcuUnavailable(unittest.TestCase):
    def test_gpo_deploys_after_300s_plus_2min_timeout(self):
        antenna, mcu, uhf = build(mcu_healthy=False)
        mcu.run()
        self.assertEqual(antenna.runs, [])  # MCU path dead
        uhf.run()

        self.assertEqual(antenna.runs, [(420, "GPO")])  # 300 s delay + 120 s timeout
        self.assertEqual(antenna.event_times("A1", "ON"), [420])
        self.assertEqual(antenna.event_times("B1", "ON"), [425])
        self.assertEqual(antenna.event_times("A1", "OFF"), [430])
        self.assertEqual(antenna.event_times("B1", "OFF"), [435])
        self.assertTrue(antenna.deployed)

    def test_gpo_path_blocked_stops_after_four_loops(self):
        antenna, mcu, uhf = build(mcu_healthy=False, gpo_fault=True)
        uhf.run()
        self.assertEqual([t for t, _ in antenna.runs], [420, 560, 700, 840])
        self.assertFalse(antenna.deployed)

    def test_uhf_alternates_mcu_and_gpo_attempts(self):
        antenna, mcu, uhf = build(faulty={"A1", "B1"})  # wire 1 can never burn
        mcu.run()
        uhf.run()
        self.assertEqual(
            antenna.runs,
            [(120, "MCU"), (135, "MCU"), (300, "MCU-by-UHF"), (320, "GPO"),
             (340, "MCU-by-UHF"), (360, "GPO")],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
