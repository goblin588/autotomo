"""
Automated polarisation tomography characterisation.

Requires:
    Thorlabs PM100USB power meter
    SMC100 motor stages (1 input HWP/QWP pair, 1 tomography HWP/QWP pair)

Run with AUTOTOMO_SIM=1 to use mock hardware (no physical connection needed):
    AUTOTOMO_SIM=1 python tomo_auto.py
"""
import datetime
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

import libraries.data_processing as dpl
import libraries.plotting as cpl
import libraries.tomography as tl
from libraries.angle_menu import angle_menu
from libraries.basis_vectors import process_state_angles
from libraries.settings import (HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2, HWP_TOM_1, QWP_TOM_1,
                                HWP_OUT_2, QWP_OUT_2, COMPORT, SIM_MODE)
from libraries.notifier import notify
from polarisation_tuner import polarisation_tuner


def _tomo_stages(path: int):
    if path == 1:
        return HWP_TOM_1, QWP_TOM_1
    return HWP_OUT_2, QWP_OUT_2


def _get_powermeter(wavelength=1550, verbose=True):
    if SIM_MODE:
        from interfaces.mock import MockPowerMeter
        return MockPowerMeter(wavelength=wavelength, verbose=verbose)
    import interfaces.pm100usb as pml
    return pml.PM100USB(wavelength=wavelength, verbose=verbose)


def run_tomo(angles, path, bases, plot_type, show_plot=False, angle_table=None):
    """Tomo each input basis in bases, then plot against theory and notify.

    angle_table: prep-angle lookup passed to input_tomography (default
    basis_angles; pass process_state_angles for s{j}_{N} inputs).
    """
    print(f"Performing tomography for input states: {', '.join(bases)}")
    tl.set_fixed_waveplates(angles, path)
    hwp_tom, qwp_tom = _tomo_stages(path)
    with _get_powermeter() as pm:
        res = tl.input_tomography(qwp_tom, hwp_tom, HWP_IN, QWP_IN, pm, COMPORT,
                                  bases=bases, angle_table=angle_table)
    tl.beep()
    fit = cpl.plot_characterisation(res, graph_title=angles['title'], angles=angles,
                                    plot_type=plot_type, show_plot=show_plot, path=path)
    notify(f"{plot_type} tomo done — fit: {fit:.4f} — {angles['title']}",
           title=f"{plot_type} tomo complete",
           priority="high" if len(bases) > 2 else "default")


def fibre_tomo(bases=tl.FULL_BASES):
    """Tomo straight through the fibre: IN preps, IN_2 analyzes. No internal
    optics in between and no unitary to fit — it's measured beforehand — so
    theory is identity.
    """
    print(f"Performing fibre tomography for input states: {', '.join(bases)}")
    with _get_powermeter() as pm:
        res = tl.input_tomography(QWP_IN_2, HWP_IN_2, HWP_IN, QWP_IN, pm, COMPORT, bases=bases)
    tl.beep()
    angles = {'title': 'Fibre'}
    fit = cpl.plot_characterisation(res, graph_title=angles['title'], angles=angles,
                                    plot_type='Fibre', show_plot=True, identity=True)
    notify(f"Fibre tomo done — fit: {fit:.4f}",
           title="Fibre tomo complete", priority="default")


def s_tomo(angles, path):
    """Tomo the s{j}_{N} process states for the chosen unitary N."""
    N = angles.get('N', '3')
    s_keys = tuple(k for k in process_state_angles if k.endswith(f'_{N}'))
    j = input(f"Which s state for N={N}? (0-{len(s_keys) - 1}, or Enter for all): ").strip()
    if j:
        key = f's{j}_{N}'
        if key not in process_state_angles:
            print(f"No state {key}. Options: {', '.join(s_keys)}")
            return
        bases = (key,)
    else:
        bases = s_keys
    run_tomo(angles, path, bases, plot_type=f'S{N}', angle_table=process_state_angles)


def multi_run(angles, path: int = 2):
    n = int(input("Collect how many measurements?: "))
    tl.set_fixed_waveplates(angles, path)
    hwp_tom, qwp_tom = _tomo_stages(path)
    res_out = {}
    with _get_powermeter() as pm:
        try:
            for i in range(n):
                print(f"Performing measurement {i + 1}/{n}...")
                res_out[i] = tl.input_tomography(qwp_tom, hwp_tom, HWP_IN, QWP_IN, pm, COMPORT, bases=tl.HVAD_BASES)
                notify(f"Run {i + 1}/{n} done — {angles['title']}", title="Multi-run progress")
        except Exception as e:
            print(f"Measurement failed: {e}")
            notify(f"Measurement failed at run {len(res_out)}/{n}: {e}", title="autotomo error", priority="urgent")

    tl.beep()
    notify(f"All {n} runs complete — {angles['title']}", title="Multi-run complete", priority="high")

    for i in res_out:
        cpl.plot_characterisation(res_out[i], graph_title=angles['title'], angles=angles,
                                  plot_type=f'{i}_Multi', save_data=False, save_plot=False, show_plot=False, path=path)

    norm_data = {i: cpl.normalise_full_tomo_data(res_out[i]) for i in res_out}
    filepath = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d/%Y-%m-%d__%H-%M/")
    filepath += f"{angles['title']}_ITERATIONS"
    cpl.writeData2File(filename=filepath, data=res_out, normalised_data=norm_data, angles=angles, plot_type='Multi')


def replot(angles, path: int = 2):
    filepath = input("Path to data CSV: ").strip()
    try:
        data = dpl.load_csv_data(filepath)
        avg_data = dpl.average_measurements(data['raw_data'])
        cpl.plot_characterisation(avg_data, f"Replot — {angles['title']}", angles=angles, path=path)
    except Exception as e:
        print(f"Error loading data: {e}")


def main():
    if SIM_MODE:
        print("[SIM MODE] Running without hardware")

    print("Automated Tomography Characterisation")

    while True:
        choice = input(
            "Mode?\n"
            "  H/V/A/D/R/L  — single basis tomo\n"
            "  HV            — H + V only\n"
            "  F             — HVAD (4 input states)\n"
            "  6             — HVADRL (all 6 input states)\n"
            "  S             — s_j process state tomo\n"
            "  FIB           — fibre tomo (IN preps, IN_2 analyzes, unitary = identity)\n"
            "  M             — multi-run\n"
            "  T             — polarisation tuner\n"
            "  P             — replot saved data\n"
            "> "
        ).upper()

        if choice == 'T':
            polarisation_tuner()
            break
        if choice not in (*tl.FULL_BASES, 'HV', 'F', '6', 'S', 'FIB', 'M', 'P'):
            print("Valid inputs: H, V, A, D, R, L, HV, F, 6, S, FIB, M, T, P")
            continue

        if choice == 'FIB':
            fibre_tomo()
            break

        angles = angle_menu()
        _p = input("Output path [1/2, default 2]: ").strip()
        path = 1 if _p == '1' else 2

        if choice in tl.FULL_BASES:
            run_tomo(angles, path, (choice,), 'Single', show_plot=True)
        elif choice == 'HV':
            run_tomo(angles, path, tl.HV_BASES, 'HV', show_plot=True)
        elif choice == 'F':
            run_tomo(angles, path, tl.HVAD_BASES, 'Full')
        elif choice == '6':
            run_tomo(angles, path, tl.FULL_BASES, 'Full6')
        elif choice == 'S':
            s_tomo(angles, path)
        elif choice == 'M':
            multi_run(angles, path)
        elif choice == 'P':
            replot(angles, path)
        break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")
