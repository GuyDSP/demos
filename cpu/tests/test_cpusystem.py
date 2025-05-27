import unittest

from cpu.systems import CPUSystem


class TestCPUSystem(unittest.TestCase):

    def setUp(self):
        self.cpu_sys = CPUSystem("cpu_system")
        self.cpu_sys.T_cpu = 40.0  # simulate hot CPU to activate fan
        self.cpu_sys.run_once()

    def test_subsystems_exist(self):
        for child in ["cpu", "fan", "controler", "exchanger"]:
            self.assertIn(child, self.cpu_sys.children)

    def test_connections_work(self):
        # Test if the fan's outlet is connected to the exchanger's inlet
        self.assertAlmostEqual(
            self.cpu_sys.exchanger.fl_in.mass_flow, self.cpu_sys.fan.fl_out.mass_flow
        )
        self.assertAlmostEqual(self.cpu_sys.exchanger.fl_in.T, self.cpu_sys.fan.fl_out.T)

        # Check if the CPU received heat_flow from exchanger
        self.assertAlmostEqual(self.cpu_sys.cpu.heat_flow, self.cpu_sys.exchanger.heat_flow)

    def test_cpu_temperature_rises(self):
        # T should increase from default 20 due to power > heat_flow
        self.assertGreater(self.cpu_sys.cpu.T, 20.0)

    def test_design_method_runs(self):
        # Run design method and check if it changes the surface
        original_surface = self.cpu_sys.exchanger.surface
        self.cpu_sys.exchanger.surface = 0.001  # wrong initial guess
        self.cpu_sys.design("exchanger_surface")
        # After design, surface should have changed
        self.assertNotAlmostEqual(self.cpu_sys.exchanger.surface, original_surface)
