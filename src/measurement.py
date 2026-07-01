"""
Sets the input waveplates to the s0 state for a given unitary N.

Run with AUTOTOMO_SIM=1 to use mock hardware:
    AUTOTOMO_SIM=1 python measurement.py
"""
import libraries.tomography as tl
from libraries.basis_vectors import basis_angles
from libraries.settings import HWP_IN, QWP_IN, COMPORT, SIM_MODE

VALID_N = [k.split('_')[1] for k in basis_angles if k.startswith('s0_')]


def prepare_s0_state(N):
    key = f's0_{N}'
    if key not in basis_angles:
        raise ValueError(f"No s0 state for N={N}. Available: {VALID_N}")
    hwp_angle, qwp_angle = basis_angles[key]
    tl.move_stage(HWP_IN, hwp_angle, COMPORT)
    tl.move_stage(QWP_IN, qwp_angle, COMPORT)
    print(f"Input stages set to s0 state for N={N}  (HWP={hwp_angle:.3f}°, QWP={qwp_angle:.3f}°)")

def main():
    if SIM_MODE:
        print("[SIM MODE] Running without hardware")

    print(f"Available unitaries: {VALID_N}")
    N = input("Which unitary N? ").strip()
    prepare_s0_state(N)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")