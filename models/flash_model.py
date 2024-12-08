import numpy as np
from dataclasses import dataclass
from typing import Tuple, Union


@dataclass
class MOSFETParams:
    Vth: float  # Threshold voltage
    K: float  # Transconductance parameter
    Is0: float  # Reverse saturation current
    n: float  # Subthreshold slope factor
    Prob0: float  # Hot electron injection probability
    Va: float  # Acceleration voltage
    beta: float  # Tunneling parameter
    Vbi: float  # Built-in potential
    xi: float  # Tunneling coefficient


class FlashMemoryCell:
    def __init__(self):
        # Capacitances
        self.Cgd = 1.5e-11  # Gate-to-drain capacitance [F]
        self.Cgsr = 1e-12  # Gate-to-source capacitance (read) [F]
        self.Cgsi = 1e-12  # Gate-to-source capacitance (injection) [F]

        # MOSFET parameters
        self.pa_r = MOSFETParams(
            Vth=0.87,  # Base threshold voltage
            K=1.7e-5,  # Base transconductance
            Is0=3e-8,  # Base saturation current
            n=1.85,  # Base subthreshold slope
            Prob0=0,  # No injection for read transistor
            Va=0,  # No acceleration voltage for read
            beta=10,  # Tunneling parameter
            Vbi=5,  # Built-in potential
            xi=2.5e-8  # Tunneling coefficient
        )

        # Injection transistor parameters (modified from read transistor)
        self.pa_i = MOSFETParams(
            Vth=0.87 + 0.45,  # Higher threshold
            K=1.7e-5 * 2,  # Higher transconductance
            Is0=3e-8 * 2,  # Higher saturation current
            n=1.85 * 1.3,  # Modified subthreshold slope
            Prob0=1e-3,  # Enable injection
            Va=20,  # Enable acceleration
            beta=10,  # Same tunneling parameter
            Vbi=5,  # Same built-in potential
            xi=2.5e-8  # Same tunneling coefficient
        )

        self.kT = 0.026  # Thermal voltage [eV]
        self.m = 1  # Current smoothing parameter
        self.s = 5  # Current curve smoothing parameter

    def mosfet(self, Vfg: float, Vd: float, Vs: Union[str, float],
               pa: MOSFETParams) -> Tuple[float, float]:
        """
        Model MOSFET behavior including hot electron injection and tunneling.

        Args:
            Vfg: Floating gate voltage
            Vd: Drain voltage
            Vs: Source voltage ('z' for high impedance)
            pa: MOSFET parameters

        Returns:
            Tuple of (source current, gate current)
        """
        if Vs == 'z':
            return 0, 0

        Vds = Vd - Vs
        Is = 0

        if Vds > 0:
            # Subthreshold current
            is_sub = pa.Is0 * np.exp((Vfg - pa.Vth) / (pa.n * self.kT)) * (1 - np.exp(-Vds / self.kT))

            # Above-threshold current
            is_ab = self.s * pa.Is0 * (1 - np.exp(-Vds / self.kT))

            if Vfg - pa.Vth >= 0 and Vfg - pa.Vth < Vds:
                is_ab += pa.K / 2 * (Vfg - pa.Vth) ** 2
            elif Vfg - pa.Vth >= Vds:
                is_ab += pa.K * (Vfg - pa.Vth - Vds / 2) * Vds

            # Combine currents using smoothing function
            Is = 1.0 / (1.0 / is_sub ** self.m + 1.0 / is_ab ** self.m) ** (1 / self.m)

        # Calculate gate currents
        # Lucky electron (hot electron injection) current
        if Vfg < 0.1:
            Igl = 0
        else:
            Igl = -Is * pa.Prob0 * np.exp(-pa.Va / Vfg)

        # Tunneling current
        Vsg = Vs - Vfg
        if Vsg <= pa.Vbi:
            Igt = 0
        else:
            Igt = pa.xi * (Vsg - pa.Vbi) ** 2 * np.exp(-pa.beta / (Vsg - pa.Vbi))

        return Is, Igl + Igt

    def simulate_step(self, Qfg: float, Vd: Union[str, float],
                      Vsr: Union[str, float], Vsi: Union[str, float],
                      dt: float) -> Tuple[float, float, float, float]:
        """
        Simulate one time step of the flash memory cell.

        Args:
            Qfg: Floating gate charge
            Vd: Drain voltage ('z' for high impedance)
            Vsr: Source voltage of read transistor
            Vsi: Source voltage of injection transistor
            dt: Time step

        Returns:
            Tuple of (updated Qfg, drain current, read source current,
                     injection source current)
        """
        # Handle high impedance drain
        if Vd == 'z':
            Vd = 0

        # Calculate floating gate voltage based on capacitive coupling
        if Vsr != 'z' and Vsi != 'z':
            Vfg = (Qfg + self.Cgsr * Vsr + self.Cgd * Vd + self.Cgsi * Vsi) / \
                  (self.Cgsr + self.Cgd + self.Cgsi)
        elif Vsr != 'z' and Vsi == 'z':
            Vfg = (Qfg + self.Cgsr * Vsr + self.Cgd * Vd) / (self.Cgsr + self.Cgd)
        elif Vsr == 'z' and Vsi != 'z':
            Vfg = (Qfg + self.Cgd * Vd + self.Cgsi * Vsi) / (self.Cgd + self.Cgsi)
        else:  # Both sources at high impedance
            Vfg = (Qfg + self.Cgd * Vd) / self.Cgd

        # Calculate currents for both transistors
        Isr, Igr = self.mosfet(Vfg, Vd, Vsr, self.pa_r)  # Read transistor
        Isi, Igi = self.mosfet(Vfg, Vd, Vsi, self.pa_i)  # Injection transistor

        # Total currents
        Id = Isr + Isi  # Total drain current
        Ig = Igr + Igi  # Total gate current

        # Update floating gate charge
        Qfg = Qfg + Ig * dt

        return Qfg, Id, Isr, Isi


# Example usage
if __name__ == "__main__":
    # Create flash memory cell instance
    flash = FlashMemoryCell()

    # Initial conditions
    Qfg = 0  # Initial floating gate charge
    Vd = 5  # Drain voltage
    Vsr = 0  # Read transistor source voltage
    Vsi = 0  # Injection transistor source voltage
    dt = 1e-9  # Time step (1 ns)

    # Simulate one step
    Qfg_new, Id, Isr, Isi = flash.simulate_step(Qfg, Vd, Vsr, Vsi, dt)

    print(f"New floating gate charge: {Qfg_new:.2e} C")
    print(f"Total drain current: {Id:.2e} A")
    print(f"Read transistor current: {Isr:.2e} A")
    print(f"Injection transistor current: {Isi:.2e} A")