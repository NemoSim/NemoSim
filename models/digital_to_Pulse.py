import json
from baseModel import BaseModel
from typing import List, Optional


class DTPConfiguration:
    def __init__(self, config_path: str):
        """Initialize DTP configuration from JSON file"""
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.pulse_width = config.get('pulse_width', 5)  # Default 5µs
        self.simulation_tick = config.get('simulation_tick', 1)  # Default 1ns
        self.bit_resolution = config.get('bit_resolution', 8)  # Default 8-bit
        self.pulse_voltage = config.get('pulse_voltage', 5.0)  # Default 5V

    def get_pulse_width(self) -> float:
        return self.pulse_width

    def get_simulation_tick(self) -> float:
        return self.simulation_tick

    def get_bit_resolution(self) -> int:
        return self.bit_resolution

    def get_pulse_voltage(self) -> float:
        return self.pulse_voltage


class DTP(BaseModel):
    def __init__(self, baseModel: BaseModel, config_path: str):
        self.baseModel = baseModel
        self.config = DTPConfiguration(config_path)

        # Calculate ticks per pulse
        self.ticks_per_pulse = int(self.config.get_pulse_width() * 1000 /
                                   self.config.get_simulation_tick())  # Convert µs to ns

        # Initialize state
        self.current_value = 0  # Current digital value being processed
        self.pulses_remaining = 0  # Number of pulses to generate
        self.is_pulse_high = False  # Current pulse state
        self.pulse_tick_counter = 0  # Counter for current pulse or gap
        self.output_voltage = 0.0  # Current output voltage

    def _voltage_to_digital(self, voltage: float) -> int:
        """Convert input voltage to digital value"""
        return int(voltage)

    def _count_pulses(self, value: int) -> int:
        """Return the input value as number of pulses to generate"""
        return value if value >= 0 else 0

    def run(self) -> None:
        # Get input voltage from base model
        input_voltage = self.baseModel.get_voltage()
        new_value = self._voltage_to_digital(input_voltage)

        # Check for new input when not processing pulses
        if self.pulses_remaining == 0 and self.pulse_tick_counter == 0:
            if new_value != self.current_value:
                self.current_value = new_value
                self.pulses_remaining = self._count_pulses(new_value)
                if self.pulses_remaining > 0:
                    self.is_pulse_high = True
                    self.pulse_tick_counter = self.ticks_per_pulse
                    self.output_voltage = self.config.get_pulse_voltage()

        # Process ongoing pulse sequence
        if self.pulse_tick_counter > 0:
            self.pulse_tick_counter -= 1
            if self.pulse_tick_counter == 0:
                if self.is_pulse_high:
                    # Switch to low period
                    self.output_voltage = 0.0
                    self.is_pulse_high = False
                    self.pulse_tick_counter = self.ticks_per_pulse
                else:
                    # End of low period
                    self.pulses_remaining -= 1
                    if self.pulses_remaining > 0:
                        # Start next pulse
                        self.is_pulse_high = True
                        self.pulse_tick_counter = self.ticks_per_pulse
                        self.output_voltage = self.config.get_pulse_voltage()

    def get_voltage(self) -> float:
        return self.output_voltage

    def get_current(self) -> float:
        return 0.0


# Example usage:
if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt


    # Example base model for testing
    class TestModel(BaseModel):
        def __init__(self, test_value):
            self.test_value = test_value

        def get_voltage(self):
            return self.test_value

        def run(self):
            pass

        def get_current(self):
            return 0.0


    # Create example configuration file
    config = {
        "pulse_width": 5,  # 5µs
        "simulation_tick": 1,  # 1ns
        "bit_resolution": 2,  # 2-bit resolution (for 00,01,10,11)
        "pulse_voltage": 5.0  # 5V pulses
    }

    with open("dtp_config.json", "w") as f:
        json.dump(config, f)

    # Test all possible 2-bit values
    test_values = [0, 1, 2, 3]  # 00, 01, 10, 11
    plt.figure(figsize=(15, 8))

    for i, value in enumerate(test_values):
        # Create new DTP instance for each test
        base_model = TestModel(value)
        dtp = DTP(base_model, "dtp_config.json")

        # Run simulation for 50µs
        time_points = []
        voltages = []

        for t in range(50000):  # 50µs in ns steps
            dtp.run()
            time_points.append(t)
            voltages.append(dtp.get_voltage())

        # Plot in subplot
        plt.subplot(len(test_values), 1, i + 1)
        plt.plot(time_points, voltages)
        plt.ylabel(f'Input {value:02b}')
        plt.grid(True)

        if i == len(test_values) - 1:
            plt.xlabel('Time (ns)')

    plt.suptitle('DTP Output for Different Input Values\nShowing number of pulses: 0→0, 01→1, 10→2, 11→3')
    plt.tight_layout()
    plt.show()