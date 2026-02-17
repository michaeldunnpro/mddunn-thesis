import os
import sys

import dask.dataframe as dd
import numpy as np
import pandas as pd
from tomlkit import dumps

from . import config


def bethe_stopping_power(epsilon_mev_per_amu, electron_density, ionization_energy):
	"""Compute Bethe stopping power in keV/um for given epsilon (MeV/amu)."""
	epsilon = epsilon_mev_per_amu * 1e6 * config.Q_E / config.AMU_TO_KG
	raw = (
		2
		* np.pi
		* electron_density
		/ (epsilon * config.M_E)
		* (config.Q_E**2 / (4 * np.pi * config.EPSILON_0)) ** 2
		* np.log(4 * config.M_E * epsilon / ionization_energy)
	)
	return raw * config.J_TO_KEV / config.M_TO_MICRONS


def build_geometry_0d(diamond):
	return {
		"length_unit": "ANGSTROM",
		"electronic_stopping_correction_factor": 0.0,
		"densities": [diamond["n"] / 1e30],
	}


def build_material_parameters(diamond):
	return {
		"energy_unit": "EV",
		"mass_unit": "AMU",
		"Eb": [diamond["Eb"]],
		"Es": [diamond["Es"]],
		"Ec": [diamond["Ec"]],
		"Ed": [diamond["Ed"]],
		"Z": [diamond["Z"]],
		"m": [diamond["m"]],
		"interaction_index": [0, 0],
		"surface_binding_model": {"PLANAR": {"calculation": "INDIVIDUAL"}},
		"bulk_binding_model": "INDIVIDUAL",
	}


def build_particle_parameters(species, number_ions, angle_deg):
	return {
		"length_unit": "ANGSTROM",
		"energy_unit": "EV",
		"mass_unit": "AMU",
		"N": [number_ions],
		"m": [species["m"]],
		"Z": [species["Z"]],
		"E": [0.0],
		"Ec": [species["Ec"]],
		"Es": [species["Es"]],
		"pos": [[0.0, 0.0, 0.0]],
		"dir": [
			[
				np.cos(angle_deg * np.pi / 180.0),
				np.sin(angle_deg * np.pi / 180.0),
				0.0,
			]
		],
	}


def run_species_simulation(
	species,
	energies_mev_per_amu,
	output_filename,
	rustbca_dir,
	output_dir,
	options,
	material_parameters,
	geometry_input,
	run_sim=config.DEFAULT_RUN_SIM,
	mode=config.DEFAULT_MODE,
	number_ions=config.DEFAULT_NUMBER_IONS,
	angle_deg=config.DEFAULT_ANGLE_DEG,
	energy_read_range=None,
	clear_output=None,
):
	if energy_read_range is None:
		energy_read_range = np.linspace(
			config.DEFAULT_ENERGY_RANGE_START,
			config.DEFAULT_ENERGY_RANGE_STOP,
			config.DEFAULT_ENERGY_RANGE_BINS,
		)

	energies_in = energies_mev_per_amu * 1e6 * species["m"]

	os.chdir(rustbca_dir)
	sys.path.append(os.path.join(os.getcwd(), "scripts"))

	particle_parameters = build_particle_parameters(species, number_ions, angle_deg)

	stopping_data = []
	for energy_mev_per_amu, energy_ev in zip(energies_mev_per_amu, energies_in):
		print(
			f"Running simulation for incident energy: {energy_mev_per_amu} MeV/amu"
		)
		particle_parameters["E"] = [energy_ev]
		input_data = {
			"options": options,
			"material_parameters": material_parameters,
			"particle_parameters": particle_parameters,
			"geometry_input": geometry_input,
		}

		input_string = dumps(input_data).replace("\r", "")
		with open("examples/input_file.toml", "w") as input_file:
			input_file.write(input_string)

		if run_sim:
			os.system(f"cargo run --release {mode} examples/input_file.toml")

		loss_df = (
			dd.read_csv(
				"input_fileenergy_loss.output",
				header=None,
				dtype=float,
				blocksize="64MB",
			)
			.dropna()
		)

		depth_col = 4
		energy_cols = [2, 3]
		bin_edges = energy_read_range
		hist = np.zeros(len(bin_edges) - 1)

		for partition in loss_df.to_delayed():
			chunk = partition.compute()
			if len(chunk) > 0:
				depth = chunk.iloc[:, depth_col].values
				energy = (
					chunk.iloc[:, energy_cols[0]].values
					+ chunk.iloc[:, energy_cols[1]].values
				)
				chunk_hist, _ = np.histogram(depth, bins=bin_edges, weights=energy)
				hist += chunk_hist

		if hist.sum() == 0:
			print("No energy loss data")
			energy_density = np.zeros_like(hist, dtype=float)
		else:
			widths = np.diff(bin_edges)
			energy_density = np.divide(
				hist,
				widths * number_ions,
				out=np.zeros_like(hist, dtype=float),
				where=widths != 0,
			)

		widths = np.diff(bin_edges)
		range_min = 0.0
		range_max = 35000.0
		mask = (bin_edges[:-1] >= range_min) & (bin_edges[:-1] < range_max)
		energy_in_range = np.sum(energy_density[mask] * widths[mask])
		percent_loss_in_range = (energy_in_range / energy_ev) * 100.0
		stopping_power = energy_in_range / (range_max - range_min)
		stopping_power_keV_per_um_per_Z2 = (
			(stopping_power * 1e-3) / (1e-4) / (species["Z"] ** 2)
		)

		stopping_data.append(
			{
				"Incident Energy (MeV/amu)": energy_mev_per_amu,
				"Stopping Power (KeV/um/Z^2)": stopping_power_keV_per_um_per_Z2,
				"Percent Energy Loss (%)": percent_loss_in_range,
			}
		)

		if clear_output:
			clear_output()

	os.chdir(output_dir)
	stopping_powers_df = pd.DataFrame(stopping_data)
	stopping_powers_df.to_csv(output_filename, index=False)
	print(
		f"{species['name'].capitalize()} ion simulation and data processing complete."
	)
	return stopping_powers_df
