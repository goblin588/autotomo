"""
Manually set waveplate stage pairs to a named basis or specific angles.
"""
import libraries.tomography as tl
from libraries.basis_vectors import basis_angles
from libraries.settings import HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2, HWP_TOM, QWP_TOM, COMPORT

_PAIRS = {
    'in':  (HWP_IN,   QWP_IN,   "Input     (HWP_IN  / QWP_IN)"),
    'in2': (HWP_IN_2, QWP_IN_2, "Input 2   (HWP_IN_2 / QWP_IN_2)"),
    'tom': (HWP_TOM,  QWP_TOM,  "Tomo      (HWP_TOM / QWP_TOM)"),
}


def _beep():
    print('\a', end='', flush=True)


def _set_pair(hwp, qwp, label):
    val = input(f"  {label}\n  Basis (H/V/A/D/R/L) or 'manual': ").strip().upper()
    if val in basis_angles:
        tl.move_stage(hwp, basis_angles[val][0], COMPORT)
        tl.move_stage(qwp, basis_angles[val][1], COMPORT)
        print(f"  Set to |{val}⟩  (HWP={basis_angles[val][0]:.2f}°, QWP={basis_angles[val][1]:.2f}°)")
    elif val == 'MANUAL':
        hwp_angle = float(input("    HWP angle (deg): "))
        qwp_angle = float(input("    QWP angle (deg): "))
        tl.move_stage(hwp, hwp_angle, COMPORT)
        tl.move_stage(qwp, qwp_angle, COMPORT)
        print(f"  Set to HWP={hwp_angle:.2f}°, QWP={qwp_angle:.2f}°")
    else:
        print(f"  Unrecognised — skipping.")


def main():
    print("Stage pairs:  in  |  in2  |  tom  |  all")
    while True:
        choice = input("Which pair? (or Enter to finish): ").strip().lower()
        if choice in ('', 'done'):
            break
        elif choice == 'all':
            for hwp, qwp, label in _PAIRS.values():
                _set_pair(hwp, qwp, label)
        elif choice in _PAIRS:
            hwp, qwp, label = _PAIRS[choice]
            _set_pair(hwp, qwp, label)
        else:
            print("  Options: in, in2, tom, all")
    _beep()


if __name__ == "__main__":
    main()
