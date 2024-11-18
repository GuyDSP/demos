from cosapp.systems import System


class CPU(System):
    """
    Evaluate thermal power generated by CPU
    """

    def setup(self):
        # inputs
        self.add_inward("usage", 20.0, desc="Usage percentage")
        self.add_inward("tdp", 105.0, unit="W", desc="Thermal Design Power")
        self.add_inward("heat_flow", 0.0, unit="W", desc="Exit thermal flow")
        self.add_inward("heat_capacity", 20.0, "J/K", desc="CPU heat capacity")
        self.add_inward("T", 20.0, unit="degC", desc="Metal temperature")

        self.add_inward("expected_next_T", 0.0, unit="degC", desc="")

        # outputs
        self.add_outward("power", 20.0, unit="W", desc="Power")
        self.add_outward("heat_flow_balance", 0.0, unit="W", desc="Power")

        # transients
        self.add_transient("T", der="heat_flow_balance / heat_capacity", desc="Enthalpy delta")
        self.add_outward("next_T")

    def compute(self):
        self.power = self.tdp * self.usage / 100.0
        self.heat_flow_balance = self.power - self.heat_flow

        self.next_T = (self.heat_flow_balance / self.heat_capacity) + self.T