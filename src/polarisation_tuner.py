"""
Interactive polarisation tuner: toggle prepared bases (or rotate H/D to V out)
while adjusting fibre paddles. Sibling of set_stage_angles.py.

Run with AUTOTOMO_SIM=1 or --sim for mock hardware.
"""
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

import libraries.tomography as tl
from libraries.basis_vectors import basis_angles, tomo_angles
from libraries.settings import (HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2,
                                HWP_OUT_2, QWP_OUT_2, COMPORT)


def set_stages(basis_in, basis_out):
    """IN preps basis_in; IN_2 analyzes for basis_out (mounted QWP-then-HWP,
    same as TOM_1/OUT_2, so it needs tomo_angles, not basis_angles)."""
    tl.move_stage(HWP_IN,   basis_angles[basis_in.upper()][0],  COMPORT)
    tl.move_stage(QWP_IN,   basis_angles[basis_in.upper()][1],  COMPORT)
    tl.move_stage(HWP_IN_2, tomo_angles[basis_out.upper()][0],  COMPORT)
    tl.move_stage(QWP_IN_2, tomo_angles[basis_out.upper()][1],  COMPORT)


def set_stages_loop(basis_in, basis_out):
    tl.move_stage(HWP_IN_2,  basis_angles[basis_in.upper()][0],  COMPORT)
    tl.move_stage(QWP_IN_2,  -basis_angles[basis_in.upper()][1],  COMPORT)
    tl.move_stage(HWP_OUT_2,  basis_angles[basis_out.upper()][0], COMPORT)
    tl.move_stage(QWP_OUT_2,  -basis_angles[basis_out.upper()][1], COMPORT)


# D->V output rotation isn't a basis state, so it isn't in basis_angles.
# IN_2/OUT_2 are mounted QWP-then-HWP: HWP(-22.5)@QWP(-45)@D == V exactly
# (verified via optics.py) — the old (-22.5, 0) was missing the QWP term
# and sent D to R instead.
_D_TO_V_OUT = (-22.5, -45)


def set_stages_to_v(basis_in, loop):
    """Input plates always take H and prepare H or D; output plates then rotate H or D to V."""
    basis_in = basis_in.upper()
    if basis_in == 'H':
        hwp_in, qwp_in = basis_angles['H']
        hwp_out, qwp_out = basis_angles['V']
    elif basis_in == 'D':
        hwp_in, qwp_in = basis_angles['D']
        if loop:
            qwp_in = -qwp_in  # loop QWPs are mounted backwards
        hwp_out, qwp_out = _D_TO_V_OUT
    else:
        raise ValueError(f"No V-rotation recipe for basis {basis_in}")

    if loop:
        tl.move_stage(HWP_IN_2,  hwp_in,  COMPORT)
        tl.move_stage(QWP_IN_2,  qwp_in,  COMPORT)
        tl.move_stage(HWP_OUT_2, hwp_out, COMPORT)
        tl.move_stage(QWP_OUT_2, qwp_out, COMPORT)
    else:
        tl.move_stage(HWP_IN,   hwp_in,  COMPORT)
        tl.move_stage(QWP_IN,   qwp_in,  COMPORT)
        tl.move_stage(HWP_IN_2, hwp_out, COMPORT)
        tl.move_stage(QWP_IN_2, qwp_out, COMPORT)


def polarisation_tuner():
    mode = input("Polarisation mode — 'input' (IN/IN_2) or 'loop' (IN/TOM_1/OUT_2): ").strip().lower()
    loop = mode == 'loop'
    if loop:
        _set = set_stages_loop
        print("Loop mode: IN_2 reverses input polarisation (negative angles), OUT_2 selects output basis")
    else:
        _set = set_stages
        print("Input mode: IN sets input, IN_2 sets output basis")

    this_basis = 'H'
    while True:
        print("Press enter to swap basis, type a basis letter (H/V/A/D/R/L), or 'stop' to exit")
        user_input = input()
        if user_input.lower() == 'stop':
            break
        elif user_input.upper() in basis_angles:
            _set(user_input, user_input)
            print(f"Measuring {user_input.upper()} basis")
        else:
            this_basis = 'H' if this_basis == 'D' else 'D'
            set_stages_to_v(this_basis, loop)
            print(f"Measuring {this_basis} in V OUT")
        print("READY")
        tl.beep()


if __name__ == "__main__":
    try:
        polarisation_tuner()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")
