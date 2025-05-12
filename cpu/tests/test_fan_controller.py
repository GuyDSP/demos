import unittest

from cpu.systems import FanController


class TestFanControler(unittest.TestCase):
    def setUp(self):
        self.controler = FanController("controler")

    def test_inwards_exist(self):
        self.assertEqual(self.controler["low_threshold"], 40.0)
        self.assertEqual(self.controler["high_threshold"], 60.0)
        self.assertEqual(self.controler["low_tension"], 0.0)
        self.assertEqual(self.controler["medium_tension"], 6.0)
        self.assertEqual(self.controler["max_tension"], 12.0)

    def test_outward_exists(self):
        self.assertIn("tension", self.controler.outwards)

    def test_tension_low(self):
        self.controler.T_cpu = 35.0
        self.controler.run_once()
        self.assertEqual(self.controler.tension, self.controler.low_tension)

    def test_tension_medium(self):
        self.controler.T_cpu = 50.0
        self.controler.run_once()
        self.assertEqual(self.controler.tension, self.controler.medium_tension)

    def test_tension_high(self):
        self.controler.T_cpu = 70.0
        self.controler.run_once()
        self.assertEqual(self.controler.tension, self.controler.max_tension)
