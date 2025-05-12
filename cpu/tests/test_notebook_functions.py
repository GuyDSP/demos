import unittest

import numpy as np
from cosapp.drivers import EulerExplicit, LinearDoE, NonLinearSolver, RungeKutta, RunSingleCase
from cosapp.drivers.time.scenario import Interpolator
from cosapp.recorders import DataFrameRecorder

from cpu.systems import CPUSystem


class NotebookTest(unittest.TestCase):

    def setUp(self):
        # System setup
        self.cpu = CPUSystem("cpu")
        # Define the ambient temperature and CPU usage for the hot intensive simulation
        self.tamb = np.random.uniform(39.5, 40.5, 31)
        self.usage = np.concatenate([np.random.uniform(80.0, 100.0, 20), np.full(11, 0.0)])

    def test_surface_design_40C_air(self):
        """Surface should be correctly computed when T_air = 40°C"""
        self.design = self.cpu.add_driver(NonLinearSolver("solver"))
        self.runner = self.design.add_driver(RunSingleCase("runner"))

        self.design.extend(self.cpu.design_methods["exchanger_surface"])
        self.runner.set_values(
            {
                "fan.T_air": 40.0,
                "T_cpu": 80.0,
                "cpu.usage": 100.0,
            }
        )

        self.cpu.run_drivers()
        surface = self.cpu.exchanger.surface

        # expected area > 0.01 m², surface = area of the heat exchanger
        self.assertGreater(surface, 0.01)

    def test_surface_design_30C_air(self):
        """Surface should be smaller with lower ambient temperature"""
        self.design = self.cpu.add_driver(NonLinearSolver("solver"))
        self.runner = self.design.add_driver(RunSingleCase("runner"))

        self.design.extend(self.cpu.design_methods["exchanger_surface"])
        self.runner.set_values(
            {
                "fan.T_air": 30.0,
                "T_cpu": 80.0,
                "cpu.usage": 100.0,
            }
        )

        self.cpu.run_drivers()
        surface_30 = self.cpu.exchanger.surface

        # set up the temperature at 40°C to serve as comparison
        self.runner.set_values(
            {
                "fan.T_air": 40.0,
                "T_cpu": 80.0,
                "cpu.usage": 100.0,
            }
        )

        self.cpu.run_drivers()
        surface_40 = self.cpu.exchanger.surface

        self.assertLess(surface_30, surface_40)

    def test_doe_simulation_runs(self):
        """Set up fresh drivers and recording before each test to ensure complete isolation."""
        self.doe = self.cpu.add_driver(LinearDoE("doe"))
        self.doe.add_input_var({"fan.T_air": {"lower": 30.0, "upper": 60.0, "count": 11}})
        self.recorder = self.doe.add_recorder(DataFrameRecorder(includes=["*"]))

        """Verify that the DOE simulation runs without errors and creates a recording file."""
        # Run the DOE simulation
        self.cpu.run_drivers()

        # Check if the recording file is created
        recorded_data = self.recorder.data
        self.assertGreater(len(recorded_data), 0, "No data was recorded during the simulation.")

        # Check that key expected columns exist in the recorded data
        expected_columns = ["cpu.usage", "T_cpu", "fan.T_air"]
        for col in expected_columns:
            self.assertIn(
                col, recorded_data.columns, f"Column '{col}' is missing in the recorded data."
            )

        # check the data has the right nuber of lines and assigned values
        self.assertEqual(len(recorded_data), 11, "The number of recorded data points is incorrect.")
        self.assertEqual(
            recorded_data["fan.T_air"].iloc[0], 30.0, "The first value of fan.T_air is incorrect."
        )
        self.assertEqual(
            recorded_data["fan.T_air"].iloc[-1], 60.0, "The last value of fan.T_air is incorrect."
        )

    def test_general_nominal_operational_data(self):
        """Check each step of the operating data generation"""
        # Create a time driver with the necessary solver
        self.time_driver = self.cpu.add_driver(EulerExplicit())
        self.solver = self.time_driver.add_child(NonLinearSolver("solver", max_iter=10, factor=1.0))

        # Set up time driver parameters
        self.time_driver.time_interval = (0, 30)
        self.time_driver.dt = 1.0

        # Set up the simulation scenario with interpolated values for the hot intensive scenario
        self.time_driver.set_scenario(
            init={"T_cpu": 10.0, "exchanger.h_adder": -30.0},
            values={
                "fan.T_air": Interpolator(np.stack([np.arange(0, 31, 1), self.tamb], axis=1)),
                "cpu.usage": Interpolator(np.stack([np.arange(0, 31, 1), self.usage], axis=1)),
            },
        )

        # Add a recorder for the simulation data
        self.recorder = self.time_driver.add_recorder(
            DataFrameRecorder(includes=["*"], hold=False), period=1.0
        )
        # Run the simulation
        self.cpu.run_drivers()

        # Access the recorded data
        recorded_data = self.recorder.data

        # Check if the recorded data is not empty
        self.assertGreater(len(recorded_data), 1, "No data was recorded during the simulation.")

        # Check that the expected columns exist
        expected_columns = ["fan.T_air", "cpu.usage", "T_cpu", "fan.tension", "time"]
        for col in expected_columns:
            self.assertIn(
                col, recorded_data.columns, f"Column '{col}' is missing in the recorded data."
            )
        # Check that the recorded data has the expected number of rows
        self.assertEqual(
            len(recorded_data),
            31,
            "The number of recorded data points is incorrect.",
        )
        # Check that the first and last values of the recorded data are correct
        self.assertEqual(
            recorded_data["fan.T_air"].iloc[0],
            self.tamb[0],
            "The first value of fan.T_air is incorrect.",
        )
        self.assertEqual(
            recorded_data["fan.T_air"].iloc[-1],
            self.tamb[-1],
            "The last value of fan.T_air is incorrect.",
        )
        self.assertEqual(
            recorded_data["cpu.usage"].iloc[0],
            self.usage[0],
            "The first value of cpu.usage is incorrect.",
        )
        self.assertEqual(
            recorded_data["cpu.usage"].iloc[-1],
            self.usage[-1],
            "The last value of cpu.usage is incorrect.",
        )

    def test_same_operating_conditions(self):
        """tests that the same but with different drivers"""
        # Create a time driver with the necessary solver
        self.time_driver = self.cpu.add_driver(RungeKutta(order=3))
        self.solver = self.time_driver.add_child(NonLinearSolver("solver", max_iter=10, factor=1.0))

        # Set up time driver parameters
        self.time_driver.time_interval = (0, 30)
        self.time_driver.dt = 1.0

        # Set up the simulation scenario with interpolated values for the hot intensive scenario
        self.time_driver.set_scenario(
            init={"T_cpu": 10.0},
            values={
                "fan.T_air": Interpolator(np.stack([np.arange(0, 31, 1), self.tamb], axis=1)),
                "cpu.usage": Interpolator(np.stack([np.arange(0, 31, 1), self.usage], axis=1)),
            },
        )

        # Add a recorder for the simulation data
        self.recorder = self.time_driver.add_recorder(
            DataFrameRecorder(includes=["*"], hold=False), period=1.0
        )
        # Run the simulation
        self.cpu.run_drivers()

        # Access the recorded data
        recorded_data = self.recorder.data

        # Check if the recorded data is not empty
        self.assertGreater(len(recorded_data), 1, "No data was recorded during the simulation.")

        # Check that the expected columns exist
        expected_columns = ["fan.T_air", "cpu.usage", "T_cpu", "fan.tension", "time"]
        for col in expected_columns:
            self.assertIn(
                col, recorded_data.columns, f"Column '{col}' is missing in the recorded data."
            )
        # Check that the recorded data has the expected number of rows
        self.assertEqual(
            len(recorded_data),
            31,
            "The number of recorded data points is incorrect.",
        )

    def test_simulation_runs_without_errors(self):
        """Check that the simulation executes without errors and records data."""
        # Define parameters for the simulation
        self.mass_flow_scalar = np.concatenate([np.full(10, 1.0), np.full(21, 0.0)])
        self.tamb = np.random.uniform(39.5, 40.5, 31)
        self.usage = np.concatenate([np.random.uniform(80.0, 100.0, 20), np.full(11, 0.0)])

        # Create a time driver with the necessary solver
        self.time_driver = self.cpu.add_driver(EulerExplicit())
        self.solver = self.time_driver.add_child(NonLinearSolver("solver", max_iter=10, factor=1.0))

        # Set up time driver parameters
        self.time_driver.time_interval = (0, 30)
        self.time_driver.dt = 1.0

        # Set up the simulation scenario with interpolated values for the hot intensive scenario
        self.time_driver.set_scenario(
            init={"T_cpu": 10.0, "exchanger.h_adder": -30.0},
            values={
                "fan.T_air": Interpolator(np.stack([np.arange(0, 31, 1), self.tamb], axis=1)),
                "cpu.usage": Interpolator(np.stack([np.arange(0, 31, 1), self.usage], axis=1)),
                "fan.mass_flow_scalar": Interpolator(
                    np.stack([np.arange(0, 31, 1), self.mass_flow_scalar], axis=1)
                ),
            },
        )
        # Add a recorder for the simulation data
        self.recorder = self.time_driver.add_recorder(
            DataFrameRecorder(includes=["*"], hold=False), period=1.0
        )
        # Run the simulation
        self.cpu.run_drivers()

        # Access the recorded data
        recorded_data = self.recorder.data

        # Check if the recorded data is not empty
        self.assertGreater(len(recorded_data), 1, "No data was recorded during the simulation.")

        # Check that the expected columns exist
        expected_columns = ["fan.T_air", "cpu.usage", "T_cpu", "fan.tension", "time"]
        for col in expected_columns:
            self.assertIn(
                col, recorded_data.columns, f"Column '{col}' is missing in the recorded data."
            )

        # Add noise to the recorded data to simulate dysfunction
        recorded_data["T_cpu"] += np.random.normal(-0.2, 0.2, recorded_data["T_cpu"].shape)

        # Check that the recorded data has the expected number of rows
        self.assertEqual(
            len(recorded_data),
            31,
            "The number of recorded data points is incorrect.",
        )
        # Check that the first and last values of the recorded data are correct
        self.assertEqual(
            recorded_data["fan.T_air"].iloc[0],
            self.tamb[0],
            "The first value of fan.T_air is incorrect.",
        )
        self.assertEqual(
            recorded_data["fan.T_air"].iloc[-1],
            self.tamb[-1],
            "The last value of fan.T_air is incorrect.",
        )
        self.assertEqual(
            recorded_data["cpu.usage"].iloc[0],
            self.usage[0],
            "The first value of cpu.usage is incorrect.",
        )
        self.assertEqual(
            recorded_data["cpu.usage"].iloc[-1],
            self.usage[-1],
            "The last value of cpu.usage is incorrect.",
        )
        # Check that the mass flow scalar is set to 0.0 for the last 21 time steps

        self.assertEqual(
            all(recorded_data["fan.mass_flow_scalar"][:10] == 1.0),
            True,
            f"The mass flow scalar during the first 10 is incorrect.",
        )

    def tearDown(self):
        """Clean up the CPU system after each test."""
        del self.cpu
