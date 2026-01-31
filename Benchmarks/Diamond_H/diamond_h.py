### Dependencies ###
# RustBCA
# numpy, matplotlib
# tomlkit
# dask (for large energy loss files)
# pyarrow, pandas (dependencies of dask)
###--------------###


import dask.dataframe as dd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
from libRustBCA import *


# Get script directory; will write here 
script_dir = os.path.dirname(os.path.abspath(__file__))



#############################################
## RustBCA Directory (Grabbed from root of repo) ##
###---------------------------------------###
os.chdir(script_dir + "/../../RustBCA")
###---------------------------------------###
## End RustBCA Directory                   ##
#############################################

print("Current working directory:", os.getcwd()) # Confirm directory

# Grab materials and formulas from scripts directory
sys.path.append(os.getcwd()+'/scripts')

import materials as m
import time
from tomlkit import dumps

'''
This example simulates the implantation of various H+ ions 
at a 0 degree angle into a C diamond target of 100 A thickness.

The geometry is as follows:

    H (Varying MeV, 0 deg)
    |
    V
__________
|        |
|   C    |
|        |
|        |

And calculates implantation profiles, reflection coefficients,
and sputtering yields. It also uses the ergonomic python functions
to compare the result of using the default values for He on C with
the custom values of this input file.

It creates an input file as a nested dictionary which is written to
a TOML file using tomlkit.

It runs the input file with cargo run --release and reads the output files.
'''

run_sim = True
mode = '0D'
number_ions = 500 # higher energies allow smaller numbers of ions
angle = 0.1   # degrees; measured from surface normal

'''
For organizational purposes, species are commonly defined in dictionaries.
Additional examples can be found in scripts/materials.py, but values 
should be checked for correctness before use. Values are explained
in the relevant sections below.
'''
hydrogen = m.hydrogen

# Gong et. all parameters for Diamond
diamond = {
    'symbol': 'C',
    'name': 'carbon',
    'Z': 6.0,
    'm': 12.011, # AMU 
    'Es': 7.41, # eV
    'Ec': 0.1, # eV, reasonable for cutoff
    'Eb': 7.36, # eV
    'Ed': 52.0, # eV
    'n': 1.76e29, # 1/m^3
}



# species definitions
ion = hydrogen
target1 = diamond

# geometry definitions
layer_thicknesses = [100.0]
layer_1_densities = [diamond["n"]/10**30, 0.0] # 1/A^3

options = {
    'name': 'input_file',
    'track_trajectories': False, # whether to track trajectories for plotting; memory intensive
    'track_recoils': False, # whether to track recoils; must enable for sputtering
    'track_recoil_trajectories': False, # whether to track recoil trajectories for plotting
    'track_displacements': False, # whether to track collisions with T > Ed for each species
    'track_energy_losses': True, # whether to track detailed collision energies; memory intensive
    'write_buffer_size': 2048, # how big the buffer is for file writing
    'weak_collision_order': 0, # weak collisions at radii (k + 1)*r; enable only when required
    'suppress_deep_recoils': False, # suppress recoils too deep to ever sputter
    'high_energy_free_flight_paths': False, # SRIM-style high energy free flight distances; use with caution
    'num_threads': 4, # number of threads to run in parallel
    'num_chunks': 100, # code will write to file every nth chunk; for very large simulations, increase num_chunks
    'electronic_stopping_mode': 'INTERPOLATED', # Previously 'LOW_ENERGY_NONLOCAL', leads to order of magnitude errors. Use 'INTERPOLATED' instead.
    'mean_free_path_model': 'LIQUID', # liquid is amorphous (constant mean free path); gas is exponentially-distributed mean free paths
    'interaction_potential': [['ZBL']], # ZBL potential chosen for all interactions
    'scattering_integral': [
        [
            {
                'GAUSS_MEHLER': {'n_points': 6}
            }
        ]
    ],

    'root_finder': [
        [
            {
                'NEWTON': {
                    'max_iterations': 100,
                    'tolerance': 1e-6
                }
            }
        ]
    ],
}

# material parameters are per-species
material_parameters = {
    'energy_unit': 'EV',
    'mass_unit': 'AMU',
    # bulk binding energy; typically zero as a model choice
    'Eb': [
        target1["Eb"],
    ],
    # surface binding energy
    'Es': [
        target1["Es"],    ],
    # cutoff energy - particles with E < Ec stop
    'Ec': [
        target1["Ec"]
    ],
    # displacement energy - only used to track displacements
    'Ed': [
        target1["Ed"]],
    # atomic number
    'Z': [
        target1["Z"]
    ],
    # atomic mass
    'm': [
        target1["m"]
    ],
    # used to pick interaction potential from matrix in [options]
    'interaction_index': [0, 0],
    'surface_binding_model': {
        "PLANAR": {'calculation': "INDIVIDUAL"}
    },
    'bulk_binding_model': 'INDIVIDUAL'
}

geometry_0D = {
    'length_unit': 'ANGSTROM',
    # used to correct nonlocal stopping for known compound discrpancies
    'electronic_stopping_correction_factor': 1.0,
    # number densities of each species
    'densities': [diamond["n"] / 1e30]
}

stopping_data = [] # Collect stopping powers here in list

particle_parameters = {
    'length_unit': 'ANGSTROM',
    'energy_unit': 'EV',
    'mass_unit': 'AMU',
    # number of computational ions of this species to run at this energy
    'N': [number_ions],
    # atomic mass
    'm': [ion["m"]],
    # atomic number
    'Z': [ion["Z"]],
    # incidenet energy 
    'E': [0.0], # Changed in loop
    # cutoff energy - if E < Ec, particle stops
    'Ec': [ion["Ec"]],
    # surface binding energy
    'Es': [ion["Es"]],
    # initial position - if Es significant and E low, start (n)^(-1/3) above surface
    # otherwise 0, 0, 0 is fine; most geometry modes have surface at x=0 with target x>0
    'pos': [[0.0, 0.0, 0.0]],
    # initial direction unit vector; most geometry modes have x-axis into the surface
    'dir': [
        [
            np.cos(angle*np.pi/180.0),
            np.sin(angle*np.pi/180.0),
            0.0
        ]
        ],
    }


# Loop over incident energies
for incident_energy in np.arange(1.6e6, 6.1e6, 0.1e6):
    print(f'Running simulation for incident energy: {incident_energy} eV')
    particle_parameters['E'] = [incident_energy]
    input_data = {
        'options': options,
        'material_parameters': material_parameters,
        'particle_parameters': particle_parameters,
        'geometry_input': geometry_0D
    }

    # Attempt to cleanup line endings
    input_string = dumps(input_data).replace('\r', '')
    with  open('examples/input_file.toml', 'w') as input_file:
        input_file.write(input_string)

    if run_sim:
        os.system(f'cargo run --release {mode} examples/input_file.toml')

    # Read CSV in chunks to avoid memory issues
    loss_df = dd.read_csv('input_fileenergy_loss.output',
                    header=None,
                    dtype= float,
                    blocksize="64MB").dropna()
    
    # Process histogram in chunks without loading all data into memory
    depth_col = 4
    energy_cols = [2, 3]
    
    bin_edges = np.linspace(0.0, 300000.0, 10001)
    hist = np.zeros(len(bin_edges) - 1)
    
    # Process in chunks
    for partition in loss_df.to_delayed():
        chunk = partition.compute()
        if len(chunk) > 0:
            depth = chunk.iloc[:, depth_col].values
            energy = chunk.iloc[:, energy_cols[0]].values + chunk.iloc[:, energy_cols[1]].values
            chunk_hist, _ = np.histogram(depth, bins=bin_edges, weights=energy)
            hist += chunk_hist
    
    loss = None  # Don't need full array anymore

    if hist.sum() == 0:
        print('No energy loss data')
    else:
        # Histogram energy loss data already computed above
        # Total x coordinate range is 0 to 300000 A with 10000 bins
        widths = np.diff(bin_edges)
        energy_density = np.divide(
            hist,
            widths * number_ions,
            out=np.zeros_like(hist, dtype=float),
            where=widths != 0
        )

    total_loss_per_ion = hist.sum() / number_ions

    print('Total energy loss per ion:', total_loss_per_ion, 'eV')

    # Print energy per ion in particular range (e.g., 0 to 1000 A)
    range_min = 0.0 # Depletion region
    range_max = 35000.0 #  End of target
    mask = (bin_edges[:-1] >= range_min) & (bin_edges[:-1] < range_max)
    energy_in_range = np.sum(energy_density[mask] * widths[mask])
    percent_loss_in_range = (energy_in_range / incident_energy) * 100.0
    stopping_power = energy_in_range / (range_max - range_min)
    print(f'Energy loss per ion in range {range_min} A to {range_max} A: {energy_in_range} eV ({percent_loss_in_range:.2f}%)')
    print(f'Stopping power in range {range_min} A to {range_max} A: {stopping_power} eV/A/ion')
    stopping_data.append({
        'Incident Energy (eV)': incident_energy,
        'Stopping Power (eV/A/ion)': stopping_power,
        'Percent Energy Loss (%)': percent_loss_in_range
    })

# Revert to script directory for output
os.chdir(script_dir)


print(stopping_data) # Stopping power data if csv write fails
# Write to file
stopping_powers_df = pd.DataFrame(stopping_data)
stopping_powers_df.to_csv('diamond_h_stopping_powers.csv', index=False)
