import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import interpolate
import pandas as pd
import os
# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Read in stopping power data and reference data
stopping_data = pd.read_csv('diamond_he_stopping_powers.csv')
reference_data  = pd.read_csv('reference_stopping_power.csv')   

#

mass = 4.002602  # Atomic mass of Helium
z = 2          # Atomic number of Helium

# Transform to common units
stopping_data['Incident Energy (MeV/amu)'] = stopping_data['Incident Energy (eV)'] / 1e6 / mass
stopping_data['Stopping Power (keV/µm/ion)/Z^2'] = stopping_data['Stopping Power (eV/A/ion)'] * 10 / (z**2)

# Print the data to verify
print(stopping_data)
print(reference_data)

# Sort by dataset


spline_rustbca = interpolate.make_interp_spline(
    stopping_data['Incident Energy (MeV/amu)'],
    stopping_data['Stopping Power (keV/µm/ion)/Z^2'],
    k=3
)

# Plot spline for data range
energy_range = np.linspace(
    stopping_data['Incident Energy (MeV/amu)'].min(),
    stopping_data['Incident Energy (MeV/amu)'].max(),
    500
)
# Load measured data from studies
study_measured_data = reference_data[reference_data['Data Series'] == 'ALPHA']
smoothed_rustbca = spline_rustbca(energy_range)
# Create plot
plt.figure(figsize=(10, 6))
plt.plot(energy_range, smoothed_rustbca, label='RustBCA Simulation (Spline)', color='green', linestyle='--')
ax = sns.scatterplot(x=study_measured_data['ENERGY / A (MeV/amu)'], y=study_measured_data['STOPPING POWER / Z₁² (keV/um)'])
plt.xlabel('Incident Energy (MeV/amu)')
plt.ylabel('Stopping Power (keV/µm)/Z^2')
plt.title('Stopping Power of Helium Ions in Diamond')
plt.legend()
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.tight_layout()
plt.loglog()
plt.show()