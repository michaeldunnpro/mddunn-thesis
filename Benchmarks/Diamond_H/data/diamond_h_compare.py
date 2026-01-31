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
stopping_data = pd.read_csv('stopping_power_diamond_h.csv')
reference_data  = pd.read_csv('reference_stopping_power.csv')   

#


# Transform to common units
stopping_data['Incident Energy (MeV/amu)'] = stopping_data['Incident Energy (eV)'] / 1e6
stopping_data['Stopping Power (keV/µm/ion)'] = stopping_data['Stopping Power (eV/A/ion)'] * 10

# Print the data to verify
print(stopping_data)
print(reference_data)

# Sort by dataset
study_measured_data = reference_data[reference_data['Data series label'] == 'Measured']
study_old_measure = reference_data[reference_data['Data series label'] == 'Fearick et al. 1980']
study_srim_data = reference_data[reference_data['Data series label'] == 'SRIM simulation']

# Verify with print
print(study_measured_data)
print(study_srim_data)

# Spline study SRIM data for smooth curve
spline_srim = interpolate.make_interp_spline(
    study_srim_data['X Value (MeV/amu)'],
    study_srim_data['Y Value (keV/µm)'],
    k=3
)

spline_rustbca = interpolate.make_interp_spline(
    stopping_data['Incident Energy (MeV/amu)'],
    stopping_data['Stopping Power (keV/µm/ion)'],
    k=3
)

# Plot spline for data range
energy_range = np.linspace(
    study_srim_data['X Value (MeV/amu)'].min(),
    study_srim_data['X Value (MeV/amu)'].max(),
    500
)
smoothed_srim = spline_srim(energy_range)
smoothed_rustbca = spline_rustbca(energy_range)
# Create plot
plt.figure(figsize=(10, 6))
plt.plot(energy_range, smoothed_srim, label='SRIM Simulation (Spline)', color='blue', linestyle='--')
plt.plot(energy_range, smoothed_rustbca, label='RustBCA Simulation (Spline)', color='green', linestyle='--')
ax = sns.scatterplot(x=study_measured_data['X Value (MeV/amu)'], y=study_measured_data['Y Value (keV/µm)'], label='Crjnac et al. 2022', color='black', marker='o')
ax.errorbar(
    study_measured_data['X Value (MeV/amu)'],
    study_measured_data['Y Value (keV/µm)'],
    yerr=study_measured_data['Uncertainty (keV/µm)'],
    fmt='none',
    ecolor='black',
    capsize=5
)
sns.scatterplot(x=study_old_measure['X Value (MeV/amu)'], y=study_old_measure['Y Value (keV/µm)'], label='Fearick et al. 1980', color='red', marker='s')
plt.xlabel('Incident Energy (MeV/amu)')
plt.ylabel('Stopping Power (keV/µm)')
plt.title('Stopping Power of Hydrogen Ions in Diamond')
plt.legend()
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.tight_layout()
plt.show()