import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import argparse

def read_values(filename):
    with open(filename, 'r') as file:
        values = [float(line.strip()) for line in file]
    return values

def plot_values_over_time(current_values, vm_values, vout_values, dt=0.0001, layer_idx=0, neuron_idx=0):
    time = np.arange(0, len(current_values) * dt, dt)
    plt.figure(figsize=(12, 8))

    plt.subplot(3, 1, 1)
    plt.plot(time, current_values)
    plt.xlabel('Time (s)')
    plt.ylabel('Current (I_in)')
    plt.title(f'Input Current Over Time (Layer {layer_idx}, Neuron {neuron_idx})')
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(time, vm_values)
    plt.xlabel('Time (s)')
    plt.ylabel('Membrane Potential (Vm)')
    plt.title(f'Membrane Potential Over Time (Layer {layer_idx}, Neuron {neuron_idx})')
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(time, vout_values)
    plt.xlabel('Time (s)')
    plt.ylabel('Output Voltage (Vout)')
    plt.title(f'Output Voltage Over Time (Layer {layer_idx}, Neuron {neuron_idx})')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot neuron data from simulation output.')
    parser.add_argument('working_dir', type=str, help='Path to the working directory containing the output files.')
    args = parser.parse_args()

    working_dir = args.working_dir

    target_layer = int(input("Enter the target layer index: "))
    target_neuron = int(input("Enter the target neuron index: "))

    Iin_files = sorted(glob.glob(os.path.join(working_dir, 'Iins*.txt')))
    Vm_files = sorted(glob.glob(os.path.join(working_dir, 'vms*.txt')))
    Vout_files = sorted(glob.glob(os.path.join(working_dir, 'Vouts*.txt')))

    neuron_found = False
    for Iin_file, Vm_file, Vout_file in zip(Iin_files, Vm_files, Vout_files):
        try:
            layer_idx = int(os.path.basename(Iin_file)[4])
            neuron_idx = int(os.path.basename(Iin_file)[5:-4])
        except ValueError:
            print(f"Skipping file with unexpected name format: {Iin_file}")
            continue

        if layer_idx == target_layer and neuron_idx == target_neuron:
            current_values = read_values(Iin_file)
            vm_values = read_values(Vm_file)
            vout_values = read_values(Vout_file)
            plot_values_over_time(current_values, vm_values, vout_values, layer_idx=layer_idx, neuron_idx=neuron_idx)
            neuron_found = True
            break

    if not neuron_found:
        print(f"No data found for layer {target_layer}, neuron {target_neuron}.")
