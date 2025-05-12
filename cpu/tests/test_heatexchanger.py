import unittest

from cpu.ports import FluidPort
from cpu.systems import HeatExchanger


class TestHeatExchanger(unittest.TestCase):
    def setUp(self):
        self.exchanger = HeatExchanger("exchanger")
        self.exchanger.fl_in.mass_flow = 0.5  # kg/s
        self.exchanger.fl_in.T = 25.0  # degC

    def test_inwards_exist(self):
        self.assertEqual(self.exchanger["T_cpu"], 0.0)
        self.assertEqual(self.exchanger["surface"], 0.01)
        self.assertEqual(self.exchanger["cp"], 1004.0)
        self.assertEqual(self.exchanger["h_natural"], 10)
        self.assertEqual(self.exchanger["h_forced"], 100)
        self.assertEqual(self.exchanger["h_adder"], 0.0)
        self.assertEqual(self.exchanger["max_mass_flow"], 1.0)

    def test_outputs_exist(self):
        self.assertIn("fl_out", self.exchanger.outputs)
        self.assertIn("heat_flow", self.exchanger.outwards)
        self.assertIn("h", self.exchanger.outwards)

    def test_compute(self):
        self.exchanger.run_once()

        # Expected h = 10 + 100 * (0.5 / 1.0) + 0 = 60
        self.assertAlmostEqual(self.exchanger.h, 60.0)

        # Expected heat_flow = 60 * (0 - 25) * 0.01 = -15.0
        self.assertAlmostEqual(self.exchanger.heat_flow, -15.0)

        # Expected T_out = 25 + (30 / 1004) ≈ 25.0299
        self.assertAlmostEqual(self.exchanger.fl_out.T, 25 - 15.0 / 1004, places=4)

        # Check mass flow conservation
        self.assertEqual(self.exchanger.fl_out.mass_flow, self.exchanger.fl_in.mass_flow)
