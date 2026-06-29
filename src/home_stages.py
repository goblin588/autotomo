"""
Check homing status of all known stages and home as needed.
"""
import os
import sys

if '--sim' in sys.argv:
    os.environ['AUTOTOMO_SIM'] = '1'

from libraries.settings import (
    HWP_IN, QWP_IN, HWP_IN_2, QWP_IN_2,
    HWP_TOM_1, QWP_TOM_1, HWP_OUT_2, QWP_OUT_2,
    HWP_TOM_DUMP, QWP_TOM_DUMP, SIM_MODE, COMPORT
)

ALL_STAGES = {
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
}

# NOT REFERENCED states — stage needs homing
_NOT_REFERENCED = {'0A', '0B', '0C', '0D', '0E', '0F', '10', '11'}


def _check_and_home(stage_ids):
    if SIM_MODE:
        print("[SIM] Would home stages:", stage_ids)
        return

    import interfaces.smc100 as smc
    with smc.SMC100Connection(port=COMPORT) as conn:
        for sid in stage_ids:
            stage = smc.SMC100Stage(conn, smcID=sid)
            _, state = stage.get_status()
            needs_home = state in _NOT_REFERENCED
            name = ALL_STAGES.get(sid, str(sid))
            if needs_home:
                print(f"  Homing stage {sid} ({name})...")
                stage.home(waitStop=True)
                print(f"  Stage {sid} ({name}) homed.")
            else:
                print(f"  Stage {sid} ({name}) already homed — skipping.")


def main():
    if SIM_MODE:
        print("[SIM MODE]")

    print("Checking stage homing status...")

    if SIM_MODE:
        unhomed = list(ALL_STAGES.keys())
    else:
        import interfaces.smc100 as smc
        unhomed = []
        with smc.SMC100Connection(port=COMPORT) as conn:
            for sid, name in ALL_STAGES.items():
                stage = smc.SMC100Stage(conn, smcID=sid)
                _, state = stage.get_status()
                if state in _NOT_REFERENCED:
                    unhomed.append(sid)

    if not unhomed:
        print("All stages are homed.")
        return

    print("\nStages not homed:")
    for sid in unhomed:
        print(f"  {sid}: {ALL_STAGES[sid]}")

    choice = input("\nEnter stage number to home, or press Enter to home all: ").strip()

    if choice == '':
        _check_and_home(unhomed)
    else:
        try:
            sid = int(choice)
        except ValueError:
            print("Invalid input.")
            return
        if sid not in ALL_STAGES:
            print(f"Stage {sid} not recognised.")
            return
        _check_and_home([sid])

    print("Done.")


if __name__ == "__main__":
    main()
