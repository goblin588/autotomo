"""
Detect all SMC100 stages connected on COMPORT and home as needed.
"""
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

from libraries.settings import (
    HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2,
    HWP_TOM_1, QWP_TOM_1, HWP_OUT_2, QWP_OUT_2,
    HWP_TOM_DUMP, QWP_TOM_DUMP, HWP_1, QWP_1, HWP_12, QWP_12,
    SIM_MODE, COMPORT
)

# Name lookup for known stages, display-only — detection no longer depends
# on this list, so a newly wired-up stage shows up as 'unknown' instead of
# being invisible to this script.
_STAGE_NAMES = {
    HWP_IN.ID:       'HWP_IN',
    QWP_IN.ID:       'QWP_IN',
    HWP_IN_2.ID:     'HWP_IN_2',
    QWP_IN_2.ID:     'QWP_IN_2',
    HWP_TOM_1.ID:    'HWP_TOM_1',
    QWP_TOM_1.ID:    'QWP_TOM_1',
    HWP_OUT_2.ID:    'HWP_OUT_2',
    QWP_OUT_2.ID:    'QWP_OUT_2',
    HWP_TOM_DUMP.ID: 'HWP_TOM_DUMP',
    QWP_TOM_DUMP.ID: 'QWP_TOM_DUMP',
    HWP_1.ID:        'HWP_1',
    QWP_1.ID:        'QWP_1',
    HWP_12.ID:       'HWP_12',
    QWP_12.ID:       'QWP_12',
}

_NOT_REFERENCED = {'0A', '0B', '0C', '0D', '0E', '0F', '10', '11'}

# SMC100/ESP controllers on the same RS-485 bus are addressed 1-31.
_SCAN_IDS = range(1, 32)


def _detect_stages():
    """Probe every address in _SCAN_IDS on COMPORT. Returns {sid: state}
    for every address that responds. Single-shot (no retry) per address —
    an unused address should time out once, not ten times."""
    import interfaces.smc100 as smc
    found = {}
    with smc.SMC100Connection(port=COMPORT) as conn:
        for sid in _SCAN_IDS:
            stage = smc.SMC100Stage(conn, smcID=sid)
            try:
                _, state = stage.get_status(retry=1)
                found[sid] = state
            except Exception:
                continue
    return found


def _home_stage(sid):
    import interfaces.smc100 as smc
    with smc.SMC100Connection(port=COMPORT) as conn:
        stage = smc.SMC100Stage(conn, smcID=sid)
        stage.enable()
        stage.home(waitStop=True)
        stage.disable()


def main():
    if SIM_MODE:
        print("[SIM MODE] No hardware to scan — using known stages from settings.py")
        detected = {sid: '0A' for sid in _STAGE_NAMES}
    else:
        print(f"Scanning {COMPORT} for connected stages...")
        detected = _detect_stages()

    if not detected:
        print("No stages detected.")
        return

    print(f"\nFound {len(detected)} stage(s):")
    for sid in detected:
        print(f"  {sid}: {_STAGE_NAMES.get(sid, 'unknown')}")

    unhomed = [sid for sid, state in detected.items() if state in _NOT_REFERENCED]

    if not unhomed:
        print("\nAll detected stages are homed.")
        return

    print("\nStages not homed:")
    for sid in unhomed:
        print(f"  {sid}: {_STAGE_NAMES.get(sid, 'unknown')}")

    choice = input("\nEnter stage number to home, or press Enter to home all: ").strip()

    if choice == '':
        to_home = unhomed
    else:
        try:
            sid = int(choice)
        except ValueError:
            print("Invalid input.")
            return
        if sid not in detected:
            print(f"Stage {sid} not detected.")
            return
        to_home = [sid]

    for sid in to_home:
        name = _STAGE_NAMES.get(sid, 'unknown')
        print(f"  Homing stage {sid} ({name})...")
        if not SIM_MODE:
            _home_stage(sid)
        print(f"  Stage {sid} ({name}) homed.")

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — stages disabled.")
