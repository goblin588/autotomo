"""
Automated polarisation tomography characterisation.

Requires:
    Thorlabs PM100USB power meter
    SMC100 motor stages (1 input HWP/QWP pair, 1 tomography HWP/QWP pair)

Run with AUTOTOMO_SIM=1 to use mock hardware (no physical connection needed):
    AUTOTOMO_SIM=1 python tomo_auto.py
"""
import argparse
import datetime
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

import Libraries.CharPlotLib as cpl
import Libraries.TomoLibrary as tl
from Libraries.AngMenu import angle_menu
from Libraries.BasisVectors import basis_angles
from Libraries.Settings import HWP_IN, QWP_IN, QWP_TOM, HWP_TOM, HWP_IN_2, QWP_IN_2, COMPORT, SIM_MODE
from Libraries.notifier import notify


def _beep():
    print('\a', end='', flush=True)


def _get_powermeter(wavelength=1550, verbose=True):
    if SIM_MODE:
        from Interfaces.mock import MockPowerMeter
        return MockPowerMeter(wavelength=wavelength, verbose=verbose)
    import Interfaces.PM100USB as pml
    return pml.PM100USB(wavelength=wavelength, verbose=verbose)


def set_stages(basis_in, basis_out):
    tl.move_stage(HWP_IN, basis_angles[basis_in.upper()][0], COMPORT)
    tl.move_stage(QWP_IN, basis_angles[basis_in.upper()][1], COMPORT)
    tl.move_stage(HWP_IN_2, basis_angles[basis_out.upper()][0], COMPORT)
    tl.move_stage(QWP_IN_2, basis_angles[basis_out.upper()][1], COMPORT)


def polarisation_tuner():
    this_basis = 'H'
    while True:
        print("Press enter to swap basis, type a basis letter (H/V/A/D/R/L), or 'stop' to exit")
        user_input = input()
        if user_input.lower() == 'stop':
            break
        elif user_input.upper() in basis_angles:
            set_stages(user_input, user_input)
            print(f"Measuring {user_input.upper()} basis")
        else:
            if this_basis == 'D':
                this_basis = 'H'
                set_stages('H', 'V')
                print("Measuring H in V OUT")
            else:
                this_basis = 'D'
                set_stages('D', 'A')
                print("Measuring D in A OUT")
        print("READY")
        _beep()


def single_tomo(basis, angles):
    print(f"Performing tomography for single input basis |{basis}>")
    tl.move_stage(HWP_IN, basis_angles[basis][0], COMPORT)
    tl.move_stage(QWP_IN, basis_angles[basis][1], COMPORT)
    with _get_powermeter() as pm:
        res = {basis: tl.single_tomography(qwp=QWP_TOM, hwp=HWP_TOM, powermeter=pm, smc_port=COMPORT)}
    _beep()
    fit = cpl.plot_characterisation(res, graph_title=angles['title'], plot_type='Single', angles=angles, show_plot=True)
    notify(f"|{basis}⟩ tomo done — fit: {fit:.4f} — {angles['title']}", title="Single tomo complete")


def full_tomo(angles):
    print("Performing tomography for H, V, A, D input states")
    with _get_powermeter() as pm:
        res = tl.input_tomography(QWP_TOM, HWP_TOM, HWP_IN, QWP_IN, pm, COMPORT, bases=tl.HVAD_BASES)
    _beep()
    fit = cpl.plot_characterisation(res, graph_title=angles['title'], angles=angles, plot_type='Full', show_plot=False)
    notify(f"HVAD tomo done — fit: {fit:.4f} — {angles['title']}", title="Full tomo complete", priority="high")


def full6_tomo(angles):
    print("Performing tomography for all 6 input states (H, V, A, D, R, L)")
    with _get_powermeter() as pm:
        res = tl.input_tomography(QWP_TOM, HWP_TOM, HWP_IN, pm, COMPORT, bases=tl.FULL_BASES)
    _beep()
    fit = cpl.plot_characterisation(res, graph_title=angles['title'], angles=angles, plot_type='Full6', show_plot=False)
    notify(f"HVADRL tomo done — fit: {fit:.4f} — {angles['title']}", title="Full 6 tomo complete", priority="high")


def hv_tomo(angles):
    print("Performing tomography for H and V input states")
    with _get_powermeter() as pm:
        res = tl.input_tomography(QWP_TOM, HWP_TOM, HWP_IN, QWP_IN, pm, COMPORT, bases=tl.HV_BASES)
    _beep()
    fit = cpl.plot_characterisation(res, graph_title=angles['title'], angles=angles, plot_type='HV', show_plot=True)
    notify(f"HV tomo done — fit: {fit:.4f} — {angles['title']}", title="HV tomo complete")


def multi_run(angles):
    n = int(input("Collect how many measurements?: "))
    res_out = {}
    with _get_powermeter() as pm:
        try:
            for i in range(n):
                print(f"Performing measurement {i}...")
                res_out[i] = tl.input_tomography(QWP_TOM, HWP_TOM, HWP_IN, pm, COMPORT, bases=tl.HVAD_BASES)
                notify(f"Run {i+1}/{n} done — {angles['title']}", title="Multi-run progress")
        except Exception as e:
            print(f"Measurement failed: {e}")
            notify(f"Measurement failed at run {len(res_out)}/{n}: {e}", title="autotomo error", priority="urgent")

    _beep()
    notify(f"All {n} runs complete — {angles['title']}", title="Multi-run complete", priority="high")

    for i in res_out:
        cpl.plot_characterisation(res_out[i], graph_title=angles['title'], angles=angles,
                                  plot_type=f'{i}_Multi', save_data=False, save_plot=False, show_plot=False)

    norm_data = {i: cpl.normalise_full_tomo_data(res_out[i]) for i in res_out}

    filepath = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d/%Y-%m-%d__%H-%M/")
    filepath += f"{angles['title']}_ITERATIONS"
    cpl.writeData2File(filename=filepath, data=res_out, normalised_data=norm_data, angles=angles, plot_type='Multi')


def prepare_s0_state(N):
    key = f's0_{N}'
    if key not in basis_angles:
        print(f"No s0 state defined for N={N}. Available: {[k for k in basis_angles if k.startswith('s0')]}")
        return
    tl.move_stage(HWP_IN, basis_angles[key][0], COMPORT)
    tl.move_stage(QWP_IN, basis_angles[key][1], COMPORT)
    print(f"Input stages set to s0 state for N={N}")


def main():
    parser = argparse.ArgumentParser(description='Automated Tomography Characterisation')
    parser.add_argument('--sim', action='store_true', help='Run in simulation mode (no hardware required)')
    args = parser.parse_args()

    if SIM_MODE:
        print("[SIM MODE] Running without hardware")

    print("Automated Tomography Characterisation")
    angles = angle_menu()

    run = True
    while run:
        basis = input(
            "Input state for tomography?\n"
            "  H/V/A/D/R/L  — single basis\n"
            "  HV            — H + V only\n"
            "  F             — HVAD (4 input states)\n"
            "  6             — HVADRL (all 6 input states)\n"
            "  M             — multi-run\n"
            "  T             — polarisation tuner\n"
            "  S             — set s0 state\n"
            "> "
        ).upper()

        if basis in ['H', 'V', 'A', 'D', 'R', 'L']:
            single_tomo(basis, angles)
            run = False

        elif basis == 'HV':
            hv_tomo(angles)
            run = False

        elif basis == 'F':
            full_tomo(angles)
            run = False

        elif basis == '6':
            full6_tomo(angles)
            run = False

        elif basis == 'M':
            multi_run(angles)
            run = False

        elif basis == 'T':
            polarisation_tuner()
            run = False

        elif basis == 'S':
            prepare_s0_state(int(angles['N']))

        else:
            print("Valid inputs: H, V, A, D, R, L, HV, F, 6, M, T, S")


if __name__ == "__main__":
    main()