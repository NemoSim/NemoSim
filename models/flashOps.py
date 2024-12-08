import numpy as np
import matplotlib.pyplot as plt
from flash_model import FlashMemoryCell


def analyze_flash_characteristics():
    # Initialize flash cell
    flash = FlashMemoryCell()

    # Create voltage and charge arrays
    Vread = np.linspace(0, 3, 100)
    Qfg = np.array([-0.6, -0.9, -1.2, -1.5, -1.8]) * 1e-11  # Floating gate charges

    # Setup the plot
    plt.figure(figsize=(10, 6))

    # For each floating gate charge
    for qfg in Qfg:
        Iread = np.zeros(len(Vread))

        # Sweep read voltage
        for i, vread in enumerate(Vread):
            _, Iread[i], _, _ = flash.simulate_step(qfg, vread, 0, 0, 0)

        # Set minimum measurable current
        Iread[Iread < 1e-12] = 1e-12

        # Plot with markers
        plt.semilogy(Vread, Iread, 's-', linewidth=2, markersize=8,
                     markerfacecolor='white', label=f'Qfg = {qfg:.1e}C')

    # Configure plot
    plt.xlabel('V$_{Read}$ [V]', fontsize=12)
    plt.ylabel('I$_{Read}$ [A]', fontsize=12)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend(fontsize=10)

    # Set axis properties
    ax = plt.gca()
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.spines['top'].set_linewidth(2)
    ax.spines['right'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_linewidth(2)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    analyze_flash_characteristics()