import sys
import numpy as np
import matplotlib.pyplot as plt

def read_values(filename):
    with open(filename, 'r') as file:
        values = [float(line.strip()) for line in file]
    return values

def plot_values_over_time(vn_values, vout_values, Vins_values, dt=0.0000001):
    time = np.arange(0, len(vn_values) * dt, dt)
    time2 = np.arange(0, len(vn_values) * dt, dt)
    
    plt.figure(figsize=(12, 8))
    
    plt.subplot(3, 1, 1)
    plt.plot(time2, vn_values)
    plt.xlabel('Time (s)')
    plt.ylabel('Vn')
    plt.title('Potential Over Time')
    plt.grid(True)
    
    plt.subplot(3, 1, 2)
    plt.step(time, vout_values)
    plt.xlabel('Time (s)')
    plt.ylabel('Spikes')
    plt.title('Potential Over Time')
    plt.grid(True)    
    
    plt.subplot(3, 1, 3)
    plt.plot(time, Vins_values)
    plt.xlabel('Time (s)')
    plt.ylabel('input voltage (Vin)')
    plt.title('input voltage Over Time')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python script.py <Vns_filename> <Spikes_filename> <Vins_filename>")
        sys.exit(1)

    Vns_filename = sys.argv[1]
    Spikes_filename = sys.argv[2]
    Vins_filename = sys.argv[3]
    
    vn_values = read_values(Vns_filename)
    Spikes_values = read_values(Spikes_filename)
    Vins_values = read_values(Vins_filename)
    
    plot_values_over_time(vn_values, Spikes_values, Vins_values)
