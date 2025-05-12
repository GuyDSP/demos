import unittest

from cosapp.systems import System

from cpu.systems import CPU


class TestCPU(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU("cpu")

    def test_inwards_exist(self):
        # Check that inwards exist and have correct default values
        assert self.cpu["usage"] == 20.0
        assert self.cpu["tdp"] == 105.0
        assert self.cpu["T"] == 20.0
        assert self.cpu["heat_capacity"] == 20.0
        assert self.cpu["expected_next_T"] == 0.0
        assert self.cpu["heat_flow"] == 0.0

    def test_outwards_exist(self):
        # check that outwards exists
        for var in ["power", "heat_flow_balance", "next_T"]:
            self.assertIn(var, self.cpu.outwards)

    def test_compute(self):
        self.cpu.usage = 100
        self.cpu.tdp = 95
        self.cpu.heat_flow = 10
        self.cpu.heat_capacity = 50
        self.cpu.T = 40
        self.cpu.run_once()
        self.assertAlmostEqual(self.cpu.power, 95)
        self.assertAlmostEqual(self.cpu.heat_flow_balance, 85)
        self.assertAlmostEqual(self.cpu.next_T, 41.7, places=1)
