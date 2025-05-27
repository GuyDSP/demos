import unittest

import numpy as np
from cosapp.drivers import EulerExplicit, LinearDoE, NonLinearSolver, RungeKutta, RunSingleCase
from cosapp.drivers.time.scenario import Interpolator
from cosapp.recorders import DataFrameRecorder

from cpu.systems import CPUSystem


# ================================
# Reference Test Class (No Failures)
# ================================
class test_fan_no_failure_reference(unittest.TestCase):
    """Reference test class for fan system without any failures.
    This class sets up a transient simulation with fixed CPU usage and air temperature.
    Sets up a transient simulation with fixed CPU usage and air temperature.
    """

    def setUp(self):
        """Set up the simulation system, time driver, and solver before each test."""

        # set system and its drivers
        self.cpu = CPUSystem("cpu")
        self.time_driver = self.cpu.add_driver(
            EulerExplicit("euler", dt=1.0, time_interval=(0, 30))
        )
        self.solver = self.time_driver.add_child(NonLinearSolver("solver", max_iter=10, factor=1.0))

        # run scenario
        self.set_scenario()
        self.run_scenario()

    def set_optimal_scenario(self):
        """
        Defines a default scenario with normal fan operation:
        - CPU usage starts high then drops to 0 after 20s.
        - Constant air temperature for the fan.
        """

        np.random.seed(42)  # Ensure reproducibility
        self.usage = np.concatenate([np.random.uniform(80.0, 100.0, 31)])
        self.scenario = {
            "init": {"T_cpu": 10.0, "exchanger.h_adder": -30.0},
            "values": {
                "fan.T_air": 40.0,
                "cpu.usage": Interpolator(np.stack([np.arange(0, 31, 1), self.usage], axis=1)),
            },
        }

    def set_scenario(self):
        """This can be overridden by subclasses to introduce failures."""
        self.set_optimal_scenario()

    def run_scenario(self):
        """Executes the configured simulation scenario and stores the results."""
        # set time driver
        rec = self.time_driver.add_recorder(DataFrameRecorder(hold=False), period=1.0)
        self.time_driver.set_scenario(init=self.scenario["init"], values=self.scenario["values"])

        # run calculations
        self.cpu.run_drivers()
        self.data = rec.data

    def tearDown(self):
        """Optional cleanup (returns data for debugging if needed)."""
        return self.data


# ================================
# Fan Failure Test
# ================================
class test_fan_failure(test_fan_no_failure_reference):
    """
    Simulates a fan failure at t=20s (mass flow drops to zero).
    Inherits from the no-failure reference and overrides the scenario.
    """

    def set_scenario(self):
        """
        Add a mass flow scalar drop to simulate fan failure.
        """
        self.set_optimal_scenario()

        self.mass_flow = np.concatenate([np.full(20, 1), np.full(11, 0.0)])
        self.scenario["values"].update(
            {
                "fan.mass_flow_scalar": Interpolator(
                    np.stack([np.arange(0, 31, 1), self.mass_flow], axis=1)
                )
            }
        )

    def test_fan_failure(self):
        """
        Assert that the fan mass flow is zero after the failure point.
        """
        mass_flow = self.data["fan.fl_out.mass_flow"]
        np.testing.assert_array_equal(
            mass_flow[-11:].values,
            np.full(11, 0.0),
            err_msg="Mass flow should be 0 after fan failure at t=20s.",
        )


# ================================
# Fan Blade Build-up Test
# ================================
class test_fan_blade_build_up(test_fan_no_failure_reference):
    """
    Simulates a build-up on the fan blades that reduces fan speed after t=10s.
    """

    def set_scenario(self):
        """Reduces fan speed from t=10s onward to simulate blade build-up."""

        self.set_optimal_scenario()

        fan_speed = np.concatenate([np.full(10, 1), np.full(21, 0.5)])

        self.scenario["values"].update(
            {
                "fan.fan_speed_scalar": Interpolator(
                    np.stack([np.arange(0, 31, 1), fan_speed], axis=1)
                ),
            }
        )

    def test_fan_blade_build_up(self):
        """
        Assert that the fan's rotational speed has dropped to 3000 RPM after build-up.
        """

        fan_speed = self.data["fan.fan_speed"]
        np.testing.assert_array_equal(
            fan_speed[12:].values,
            np.full(19, 3000),
            err_msg="Fan speed should be 0 after blade build-up at t=10s.",
        )


# ================================
# Fan Controller Failure Test
# ================================
class test_fan_controler_failure(test_fan_no_failure_reference):
    """
    Simulates a failure in the fan controller at t=15s,
    forcing all tension levels to 8V from that point onward.
    """

    def set_scenario(self):
        """Override tension levels with conditional expressions after failure time."""

        self.set_optimal_scenario()

        self.scenario["values"].update(
            {
                "controler.low_tension": "controler.low_tension if time < 15 else 8 ",
                "controler.medium_tension": "controler.medium_tension if time < 15 else 8 ",
                "controler.high_tension": "controler.high_tension if time < 15 else 8 ",
            },
        )

    def test_controler_failure(self):
        """
        Assert that controller tension is set to 8V after t=15s.
        """

        tension = self.data["controler.tension"]
        np.testing.assert_array_equal(
            tension[16:].values,
            np.full(15, 8.0),
            err_msg="Tension should be 8V after controller failure at t=15s.",
        )
