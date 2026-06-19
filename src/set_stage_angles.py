"""
Manually set input or output waveplate stages to a specific basis or angle.
"""
from Libraries.BasisVectors import basis_angles
import Libraries.TomoLibrary as tl
from Libraries.Settings import HWP_IN, QWP_IN, QWP_TOM, HWP_TOM, HWP_IN_2, QWP_IN_2, COMPORT


def _beep():
    print('\a', end='', flush=True)


def main():
    print("Input State (H/V/A/D/R/L or press enter to skip): ", end="")
    user_input = input().upper()
    if user_input in basis_angles:
        print(f"Setting input basis |{user_input}>")
        tl.move_stage(HWP_IN, basis_angles[user_input][0], COMPORT)
        tl.move_stage(QWP_IN, basis_angles[user_input][1], COMPORT)

    print("Measure State (H/V/A/D/R/L) or type 'set' to enter angles manually: ", end="")
    user_input = input().upper()

    if user_input == 'SET':
        which = input("Set input (i) or output (o) stages? ").lower().strip()
        if which == 'i':
            qwp_angle = float(input("QWP_IN angle: "))
            tl.move_stage(QWP_IN_2, qwp_angle, COMPORT)
            hwp_angle = float(input("HWP_IN angle: "))
            tl.move_stage(HWP_IN_2, hwp_angle, COMPORT)
        elif which == 'o':
            qwp_angle = float(input("QWP_TOM angle: "))
            tl.move_stage(QWP_TOM, qwp_angle, COMPORT)
            hwp_angle = float(input("HWP_TOM angle: "))
            tl.move_stage(HWP_TOM, hwp_angle, COMPORT)
        else:
            print("Invalid selection.")

    elif user_input in basis_angles:
        print(f"Setting measurement basis |{user_input}>")
        tl.move_stage(HWP_TOM, basis_angles[user_input][0], COMPORT)
        tl.move_stage(QWP_TOM, basis_angles[user_input][1], COMPORT)
        print("READY")
        _beep()

    else:
        print("Invalid input.")


if __name__ == "__main__":
    main()
