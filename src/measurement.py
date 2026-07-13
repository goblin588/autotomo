"""
Prepare the s0 process state for a chosen unitary N:
sets HWP_IN/QWP_IN to s0_N and the fixed waveplates (IN_2/OUT_2) to that U's angles.

Run with AUTOTOMO_SIM=1 or --sim for mock hardware.
"""
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

import libraries.tomography as tl
from libraries.basis_vectors import process_state_angles
from libraries.settings import HWP_IN, QWP_IN, COMPORT, SIM_MODE
from libraries.waveplate_angles import unitaries_angles


def main():
    if SIM_MODE:
        print("[SIM MODE] Running without hardware")

    N = input(f"Which unitary N? ({'/'.join(unitaries_angles)}): ").strip()
    if N not in unitaries_angles:
        raise ValueError(f"No unitary for N={N}")

    hwp_angle, qwp_angle = process_state_angles[f's0_{N}']
    print(f"Setting HWP_IN to {hwp_angle}°, QWP_IN to {qwp_angle}° (s0_{N})")
    tl.move_stage(HWP_IN, hwp_angle, COMPORT)
    tl.move_stage(QWP_IN, qwp_angle, COMPORT)

    tl.set_fixed_waveplates(unitaries_angles[N])
    tl.beep()
    print("READY")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")
