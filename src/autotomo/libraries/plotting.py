"""
Plotting and file-saving for setup characterisations.

The physics model (getUnitary/UnitaryToProb/compute_fit/fit_m1/
fit_mirror_phases) lives in autotomo.theory — this file only draws/saves.
Re-exports the theory names most callers here already use via the `cpl`
alias, so existing call sites (tomo_auto.py, tests) keep working unchanged.
"""

import csv
import datetime
import math
import os

import matplotlib.pyplot as plt
import numpy as np

from autotomo.libraries.basis_vectors import basis_vectors, process_state_angles
from autotomo.theory import (  # noqa: F401 (re-exported for `cpl.*` callers)
    compute_fit, fit_m1, fit_mirror_phases, getUnitary, input_state_vector,
    normalise_pair, normalise_err, normalise_measurements,
    normalise_full_tomo_data, normalise_set, normalise_set_err,
    path_occupancy_prob, theory_exit_distribution, output_tomography_fit,
    UnitaryToProb, _unitary_from_angles,
)


# ── Private plot helpers ──────────────────────────────────────────────────────

def _make_directory_name(plot_type: str | None = None, note: str | None = None) -> str:
    day_dir = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d")
    if note is not None:
        day_dir = f'{day_dir}/{note}_Figures'
    if plot_type is not None:
        name = datetime.datetime.now().strftime(
            f"{day_dir}/{plot_type}_Figures_%Y-%m-%d/%Y-%m-%d__%H-%M"
        )
    else:
        name = datetime.datetime.now().strftime(f"{day_dir}/%Y-%m-%d__%H-%M")
    return name


def _subplot_grid(n: int):
    """Return (fig, axes_list) for n subplots in a 2-column layout."""
    if n == 1:
        fig, ax = plt.subplots(1, 1, figsize=(14, 8))
        return fig, [ax]
    cols = 2
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(28, 10 * rows))
    axes_flat = axes.ravel().tolist()
    for spare in axes_flat[n:]:
        spare.set_visible(False)
    return fig, axes_flat[:n]


def _render_basis_subplot(ax, basis: str, norm_slice: dict, theory: dict,
                          raw_slice: dict | None = None) -> float:
    """
    Draw measured vs theoretical bars for one input basis onto ax.
    norm_slice: normalized_data[basis]  — {state: [value, err]}
    theory:     {state: float}
    raw_slice:  data[basis]             — {state: (raw_val, raw_err)}, for mV labels
    Returns L2 fit residual.
    """
    labels = list(basis_vectors.keys())
    measured = [norm_slice[k][0] for k in labels]
    err      = [norm_slice[k][1] for k in labels]
    theory_vals = [theory[k] for k in labels]
    x = np.arange(len(labels))
    bar_width = 0.35

    bars = ax.bar(x, measured, width=bar_width, color='gold', label='Measured')

    if raw_slice is not None:
        for j, bar in enumerate(bars):
            raw_val, raw_err = raw_slice[labels[j]]
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{raw_val * 1000:.2f} ± {raw_err * 1000:.2f} mV",
                ha='center', va='bottom', fontsize=15,
            )

    ax.bar(x, theory_vals, width=bar_width, color='none', edgecolor='black',
           linestyle=':', linewidth=2, label='Theoretical')
    ax.errorbar(labels, measured, yerr=err, fmt='s', color='k')
    ax.set_title(f'|{basis}⟩ Input', fontsize=30)
    ax.set_xlabel('State', fontsize=30)
    ax.set_ylabel('Probability', fontsize=30)
    ax.set_ylim(0, 1)
    ax.set_xticks(x + bar_width / 2)
    ax.set_xticklabels(labels, fontsize=30)
    ax.tick_params(axis='y')
    ax.legend(fontsize=20)

    return float(np.linalg.norm(np.array(measured) - np.array(theory_vals)))


def _save_outputs(fig, data: dict, normalized_data: dict, angles: dict, graph_title: str,
                  directory_name: str, plot_type: str | None,
                  save_plot: bool, save_data: bool) -> None:
    if save_plot:
        try:
            savePlot(fig, graph_title='', filepath=directory_name)
        except Exception as e:
            print(f"Error saving plot: {e}\n  Retrying...")
            try:
                savePlot(fig, graph_title=graph_title, filepath=directory_name)
            except Exception as e2:
                print(f"Failed saving plot: {e2}")
        print(f"Plot saved to: {directory_name}")

    if save_data:
        try:
            saveData(graph_title='', data=data, normalised_data=normalized_data,
                     angles=angles, filepath=directory_name, plot_type=plot_type)
        except Exception as e:
            print(f"Error saving data: {e}\n  Retrying...")
            try:
                saveData(graph_title=graph_title, data=data, normalised_data=normalized_data,
                         angles=angles, filepath=directory_name, plot_type=plot_type)
            except Exception as e2:
                print(f"Failed saving data: {e2}")
        print(f"Data saved to: {directory_name}")


# ── Public plotting API ───────────────────────────────────────────────────────

def plot_characterisation(data: dict, graph_title: str, angles: dict,
                          plot_type: str | None = None, note: str | None = None,
                          save_plot: bool = True, save_data: bool = True,
                          show_plot: bool = True, path: int = 2,
                          identity: bool = False) -> float:
    """
    Plot measured vs theoretical probabilities for all input bases in data.
    Works for any number of bases — subplots scale in a 2-column layout.
    data: {input_basis: {output_state: (raw_val, raw_err)}}
    identity: skip the internal-optics unitary and use U = I (e.g. a direct
    fibre link between prep and analyzer, no PBS/mirror chain in between).
    """
    U = np.eye(4, dtype=complex) if identity else _unitary_from_angles(angles, path=path)
    normalized_data = normalise_full_tomo_data(data)
    bases = list(normalized_data.keys())

    fig, axes = _subplot_grid(len(bases))

    fit = 0.0
    for ax, basis in zip(axes, bases):
        theory = UnitaryToProb(U, input_state_vector(basis), path=path)
        fit += _render_basis_subplot(ax, basis, normalized_data[basis], theory,
                                     raw_slice=data[basis])

    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05, wspace=0.25, hspace=0.3)

    directory_name = _make_directory_name(plot_type, note)
    _save_outputs(fig, data, normalized_data, angles, graph_title, directory_name,
                  plot_type, save_plot, save_data)

    print(f"Measured value solution fit: {fit:.4f}")
    if show_plot:
        plt.show()
    return fit


_EXIT_PAIRS = (("H", "V"), ("A", "D"), ("R", "L"))


def _total_power_nested(entry: dict) -> tuple[float, float]:
    """Average the three complementary-pair sums (H+V, A+D, R+L) to
    recover total exit power with lower noise than any single pair."""
    sums, errs = [], []
    for k1, k2 in _EXIT_PAIRS:
        v1, e1 = entry[k1]
        v2, e2 = entry[k2]
        sums.append(v1 + v2)
        errs.append(math.hypot(e1, e2))
    val = sum(sums) / len(sums)
    err = math.sqrt(sum(e ** 2 for e in errs)) / len(errs)
    return val, err


def plot_exit_distribution(res: dict, angles: dict, N: str, graph_title: str,
                           plot_type: str | None = None, note: str | None = None,
                           save_plot: bool = True, save_data: bool = True,
                           show_plot: bool = True, path: int = 2) -> float:
    """
    Plot the normalised exit-bin distribution across all s{j}_{N} process
    states: one gold bar per state (measured, with errorbar) overlaid with
    a dashed-outline theory bar, styled after the sibling stochprocsim
    project's output-bin bar chart (not imported from it).

    res shape is auto-detected per state:
      - nested {state: {output_basis: (power, err)}} (output polarizer
        present — a full_tomography-style result): reduced via
        _total_power_nested.
      - flat {state: (power, err)} (no output polarizer —
        input_power_scan's result): used directly.
    """
    labels = tuple(k for k in process_state_angles if k.endswith(f'_{N}'))
    nested = isinstance(res[labels[0]], dict)
    raw = {k: (_total_power_nested(res[k]) if nested else res[k]) for k in labels}

    values = {k: v for k, (v, _) in raw.items()}
    normalized_vals = normalise_set(values)
    normalized_errs = normalise_set_err(raw, normalized_vals)
    theory_dist = theory_exit_distribution(angles, N, path=path)

    measured = [normalized_vals[k] for k in labels]
    errs = [normalized_errs[k] for k in labels]
    theory_vals = [theory_dist[k] for k in labels]
    x = np.arange(len(labels))
    fit = float(np.linalg.norm(np.array(measured) - np.array(theory_vals)))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, measured, color='gold', edgecolor='black', label='Measured')
    ax.errorbar(x, measured, yerr=errs, fmt='none', ecolor='black', capsize=4)
    ax.bar(x, theory_vals, facecolor='none', edgecolor='black',
          linestyle=':', linewidth=2, label='Theory')
    ax.set_xlabel('Output bin')
    ax.set_ylabel('Probability')
    ax.set_xticks(x)
    ax.set_xticklabels([f's{j}' for j in range(len(labels))])
    ax.set_ylim(0, 1)
    ax.set_title(f'{graph_title} — fit: {fit:.4f}')
    ax.legend()

    directory_name = _make_directory_name(plot_type, note)
    normalized_data = {k: [normalized_vals[k], normalized_errs[k]] for k in labels}
    _save_outputs(fig, raw, normalized_data, angles, graph_title, directory_name,
                 plot_type, save_plot, save_data)

    print(f"Exit-distribution fit: {fit:.4f}")
    if show_plot:
        plt.show()
    return fit


def plot_mirror(normalized_data: dict, categories: list) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    axes = axes.ravel()
    for i, (key, measurements) in enumerate(normalized_data.items()):
        normalized_values = [measurements[cat] for cat in categories]
        axes[i].bar(np.arange(len(categories)), normalized_values, color='gold', label=key)
        axes[i].set_ylim(0, 1)
        axes[i].set_title(f'{key} Normalized Measurements')
        axes[i].set_xlabel('State')
        axes[i].set_ylabel('Normalized Power')
        axes[i].set_xticks(np.arange(len(categories)))
        axes[i].set_xticklabels(categories)
        axes[i].legend()
    plt.tight_layout()
    plt.show()


# ── File I/O ──────────────────────────────────────────────────────────────────

def createDir(directory_name: str) -> int:
    try:
        os.makedirs(directory_name, exist_ok=True)
        print(f"Directory '{directory_name}' created successfully.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{directory_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return 1


def savePlot(fig, graph_title: str, filepath: str = os.getcwd()) -> None:
    if createDir(filepath):
        fig.savefig(filepath + '/' + graph_title + '_FIGURE.png')


def saveData(data: dict, normalised_data: dict, angles: dict, graph_title: str,
             plot_type: str | None = None, filepath: str = os.getcwd()) -> None:
    if createDir(filepath):
        writeData2File(filepath + '/' + graph_title + '_DATA',
                       data=data, normalised_data=normalised_data,
                       angles=angles, plot_type=plot_type)


def writeData2File(filename: str, data: dict, normalised_data: dict,
                   angles: dict, plot_type: str | None) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(f"{filename}.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if plot_type is not None:
            writer.writerow([f'PLOT TYPE: {plot_type}'])
        writer.writerow([f'DATE: {datetime.datetime.now().strftime("%Y/%m/%d @ %H:%M:%S")}'])
        writer.writerow([f'ANGLES: {angles}'])

        if '0' in data.keys() or 0 in data.keys():
            for key in data:
                writer.writerow([f'RAW DATA [{key}]: {data[key]}'])
        else:
            writer.writerow([f'RAW_DATA: {data}'])

        if '0' in normalised_data.keys() or 0 in normalised_data.keys():
            for key in normalised_data:
                writer.writerow([f'NORM_DATA[{key}]: {normalised_data[key]}'])
        else:
            writer.writerow([f'NORM_DATA: {normalised_data}'])