import unittest

from cpu.ports import FluidPort
from cpu.systems import CPU, Fan


class TestFan(unittest.TestCase):
    def setUp(self):
        self.fan = Fan("fan")

    def test_inwards_exists(self):
        # check that inwards exist and have corect default values
        assert self.fan["T_air"] == 40.0
        assert self.fan["tension"] == 0.0
        assert self.fan["design_tension"] == 12.0
        assert self.fan["mass_flow_max"] == 1.0
        assert self.fan["mass_flow_scalar"] == 1.0

    def test_outputs_exist(self):
        # check that output exists
        self.assertIsInstance(self.fan.fl_out, FluidPort)

    def test_compute_flow(self):
        # set some values and run the system
        self.fan["T_air"] = 35.0
        self.fan["tension"] = 6.0  # 50% of design_tension
        self.fan["mass_flow_max"] = 2.0
        self.fan["mass_flow_scalar"] = 1.0

        self.fan.run_once()

        expected_mass_flow = 1.0  # 1.0 * 2.0 * 6 / 12
        self.assertAlmostEqual(self.fan.fl_out.mass_flow, expected_mass_flow, places=2)
        self.assertEqual(self.fan.fl_out.T, 35.0)
