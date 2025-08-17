# NEMOSIM  
  
## Overview  
  
NEMOSIM.exe is a simulation tool that uses one input file: a json configuration file.

This configuration file defines the paths and settings for running the simulation:

- output_directory: Directory where output files will be saved.
- xml_config_path: Path to the XML configuration file for the test setup.
- data_input_file: Input data file used during the test.
- progress_interval_seconds: Time interval (in seconds) for logging progress updates.
- <xml_config_path>: Path to the supervisor XML configuration file for the test setup.
  
## Usage  

#LIF simulation :
  
1. To run the LIF network simulation, use the following command:  
  
NEMOSIM.exe .\Tests\SNN\LIF\sin_current_test\config.json
  
### Output Files  
  
The simulation generates three output files for each neuron:  
  
- Iins.txt: Shows the current input values.  
- vms.txt: Contains the membrane potential values.  
- Vouts.txt: Displays the output voltage (spikes).  
  
2. After the simulation, run the following Python script to plot the values over time:  
  
python plot_vm_to_dt.py <path_to_output_dir>

Then enter the layer index followed by the neuron index.
  
This will generate an image showing the values over time.  
  
## Generating New Input Files  
  
To create new current input values, use the input_creator.py script. Run the script and provide a formula representing the new input current with t as the variable. For example:  
  
python input_creator.py   
> "1e-10 * math.sin(2 * math.pi * t * 5 + 3 * math.pi / 2) + 1e-10"


#BIU simulation :
  
1. To run the BIU network simulation, use the following command:  
  
NEMOSIM.exe .\Tests\SNN\BIU\config.json
  
### Output Files  
  
The simulation generates three output files:  
  
- Vin.txt: Shows the synapse input values.  
- Vns.txt: Contains the Vn potential values.  
- Spikes.txt: Displays the output voltage (spikes).  
  
2. After the simulation, run the following Python script to plot the values over time:  
  
python plot_vn_to_dt.py Vns.txt Spikes.txt Vin.txt  
  
This will generate an image showing the values over time.  