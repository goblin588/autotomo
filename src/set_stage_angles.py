"""
Manually set waveplate stage pairs to a named basis or specific angles.
"""
import libraries.tomography as tl
from libraries.basis_vectors import basis_angles, tomo_angles, process_state_angles
from libraries.settings import (HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2,
                                 HWP_TOM_DUMP, QWP_TOM_DUMP,
                                 HWP_TOM_1, QWP_TOM_1, HWP_OUT_2, QWP_OUT_2,
                                 HWP_1, QWP_1, HWP_12, QWP_12,
                                 COMPORT, Waveplate)

# Input-arm pairs are HWP-then-QWP (state prep, H -> basis): basis_angles.
# Tomography-arm pairs are QWP-then-HWP (analyzer, basis -> H): tomo_angles.
# IN_2 and out2 are both mounted QWP-then-HWP, same as tom1, so they use
# tomo_angles too. Loop mode's backwards OUT_2 handling lives in
# polarisation_tuner.py, not here.
# Input arm can also be driven to the s{j}_{N} process-tomography states.
# Keys upper-cased to match the .upper() applied to user input below.
_INPUT_ANGLES = {**basis_angles, **{k.upper(): v for k, v in process_state_angles.items()}}

_PAIRS = {
    'in':   (HWP_IN,    QWP_IN,    "Input     (HWP_IN   / QWP_IN)", _INPUT_ANGLES),
    'in2':  (HWP_IN_2,  QWP_IN_2,  "Input 2   (HWP_IN_2 / QWP_IN_2)", tomo_angles),
    'dump': (HWP_TOM_DUMP, QWP_TOM_DUMP, "Tomo dump (HWP_TOM_DUMP / QWP_TOM_DUMP)", tomo_angles),
    'tom1': (HWP_TOM_1, QWP_TOM_1, "Tomo 1    (HWP_TOM_1 / QWP_TOM_1)", tomo_angles),
    'out2': (HWP_OUT_2, QWP_OUT_2, "Output 2  (HWP_OUT_2 / QWP_OUT_2)", tomo_angles),
}

# Interferometer plates (h1/q1/h2/q2 in getUnitary) — fixed, not basis-driven,
# so they don't fit _PAIRS; only need OA lookup for 'num' mode below.
_EXTRA_STAGES = (HWP_1, QWP_1, HWP_12, QWP_12)

# Map stage ID → Waveplate so OA can be applied when addressing by number
_STAGE_MAP: dict[int, Waveplate] = {
    wp.ID: wp
    for _, (hwp, qwp, _, _) in _PAIRS.items()
    for wp in (hwp, qwp)
} | {wp.ID: wp for wp in _EXTRA_STAGES}

# Single-stage name aliases, e.g. 'hin2' / 'qin2' for _PAIRS['in2'], plus the
# fixed interferometer plates. Each entry carries the angle dict/index needed
# to look up a basis for that half of a pair; extra stages get None/None
# since they're fixed, not basis-driven (see comment above _EXTRA_STAGES).
_SINGLE_STAGES: dict[str, tuple[Waveplate, dict | None, int | None]] = {
    f"h{key}": (hwp, angles, 0) for key, (hwp, qwp, _, angles) in _PAIRS.items()
} | {
    f"q{key}": (qwp, angles, 1) for key, (hwp, qwp, _, angles) in _PAIRS.items()
} | {
    'h1': (HWP_1, None, None), 'q1': (QWP_1, None, None),
    'h12': (HWP_12, None, None), 'q12': (QWP_12, None, None),
}

# Same lookup, keyed by stage ID instead of name, for addressing by number.
_STAGE_INFO_BY_ID: dict[int, tuple[dict | None, int | None]] = {
    wp.ID: (angles, idx) for wp, angles, idx in _SINGLE_STAGES.values()
}


def _move_pair(hwp, qwp, basis, angles):
    tl.move_stage(hwp, angles[basis][0], COMPORT)
    tl.move_stage(qwp, angles[basis][1], COMPORT)
    print(f"  Set to |{basis}⟩  (HWP={angles[basis][0]:.2f}°, QWP={angles[basis][1]:.2f}°)")


def _set_pair_interactive(hwp, qwp, label, angles):
    val = input(f"  {label}\n  Basis (H/V/A/D/R/L, or s0_3 etc.) or 'set' for individual angles: ").strip().upper()
    if val in angles:
        _move_pair(hwp, qwp, val, angles)
    elif val == 'SET':
        hwp_angle = float(input("    HWP angle (deg): "))
        qwp_angle = float(input("    QWP angle (deg): "))
        tl.move_stage(hwp, hwp_angle, COMPORT)
        tl.move_stage(qwp, qwp_angle, COMPORT)
        print(f"  Set to HWP={hwp_angle:.2f}°, QWP={qwp_angle:.2f}°")
    else:
        print("  Unrecognised — skipping.")


def _set_single_interactive(wp, angles, idx, label):
    prompt = f"  {label}  Basis (H/V/A/D/R/L) or angle (deg): " if angles else f"  {label}  Angle (deg): "
    val = input(prompt).strip().upper()
    if angles and val in angles:
        angle = angles[val][idx]
        tl.move_stage(wp, angle, COMPORT)
        print(f"  Set to |{val}⟩ → {angle:.2f}°")
        return
    try:
        angle = float(val)
    except ValueError:
        print("  Unrecognised — skipping.")
        return
    tl.move_stage(wp, angle, COMPORT)
    oa_note = f" (OA={wp.OA:.2f}° applied → {angle + wp.OA:.2f}°)" if wp.OA else ""
    print(f"  Set to {angle:.2f}°{oa_note}")


def main():
    prompt = (
        "Pair (eg. in), 'all', stage name (eg. h1), "
        f"stage number ({min(_STAGE_MAP)}-{max(_STAGE_MAP)}), "
        "'0' (zero all waveplates to their OA), or 'done' to quit: "
    )
    while True:
        val = input(prompt).strip().lower()

        if val in ('', 'done'):
            break

        if val == '0':
            for wp in _STAGE_MAP.values():
                tl.move_stage(wp, 0, COMPORT)
                print(f"  Stage {wp.ID} set to 0° (OA={wp.OA:.2f}°)")
        elif val == 'all':
            for hwp, qwp, label, angles in _PAIRS.values():
                _set_pair_interactive(hwp, qwp, label, angles)
        elif val in _PAIRS:
            hwp, qwp, label, angles = _PAIRS[val]
            _set_pair_interactive(hwp, qwp, label, angles)
        elif val in _SINGLE_STAGES:
            wp, angles, idx = _SINGLE_STAGES[val]
            _set_single_interactive(wp, angles, idx, val)
        else:
            try:
                stage_id = int(val)
            except ValueError:
                print("  Unrecognised — skipping.")
                continue
            wp = _STAGE_MAP.get(stage_id, Waveplate(stage_id, 0))
            angles, idx = _STAGE_INFO_BY_ID.get(stage_id, (None, None))
            _set_single_interactive(wp, angles, idx, f"Stage {stage_id}")

        tl.beep()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")
