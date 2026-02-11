'''
Simulation configuration options, file paths, and materials.
'''
import os

### File Paths ###
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUSTBCA_PATH = os.path.join(BASE_DIR, "RustBCA")
DATA_PATH = os.path.join(BASE_DIR, "data")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "Benchmarks", "Combined Fig", "Data")

### Bethe Constants (SI base) ###
EPSILON_0 = 8.854187817e-12
Q_E = 1.602176634e-19
M_E = 9.10938356e-31
N_ELECTRONS_DIAMOND = 1.76e29 * 6
J_TO_KEV = 6.242e15
M_TO_MICRONS = 1e6
AMU_TO_KG = 1.66053906660e-27
I_DIAMOND = 81.0 * Q_E

### Simulation Defaults ###
DEFAULT_RUN_SIM = True
DEFAULT_MODE = "0D"
DEFAULT_NUMBER_IONS = 100
DEFAULT_ANGLE_DEG = 0.1
DEFAULT_ENERGY_RANGE_START = 0.0
DEFAULT_ENERGY_RANGE_STOP = 3e5
DEFAULT_ENERGY_RANGE_BINS = 10001

### Options ###
options = {
    'name': 'input_file',
    'track_trajectories': False,
    'track_recoils': False,
    'track_recoil_trajectories': False,
    'track_displacements': False,
    'track_energy_losses': True,
    'write_buffer_size': 2048,
    'weak_collision_order': 0,
    'suppress_deep_recoils': False,
    'high_energy_free_flight_paths': False,
    'num_threads': os.cpu_count(),
    'num_chunks': 100,
    'electronic_stopping_mode': 'INTERPOLATED',
    'mean_free_path_model': 'LIQUID',
    'interaction_potential': [['ZBL']], 
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

### Materials ###
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
    'n': 1.76e29, # 1/m^3, atomic density of diamond
}

# Default RustBCA parameters for H, He, and Li
hydrogen = {
    'symbol': 'H',
    'name': 'hydrogen',
    'Z': 1.0,
    'm': 1.008,
    'Ec': 0.95,
    'Es': 1.5,
}

helium = {
    'symbol': 'He',
    'name': 'helium',
    'Z': 2.0,
    'm': 4.002602,
    'Ec': 1.0,
    'Es': 0.
}

lithium = {
    'symbol': 'Li',
    'name': 'lithium',
    'Z': 3.0,
    'm': 6.941,
    'Ec': 1.0,
    'Es': 1.64,
    'Eb': 0.0,
    'n': 4.63E28
}