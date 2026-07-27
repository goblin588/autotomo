"""
Functions associated with Tomography control / movement of stages.
"""

from libraries.basis_vectors import basis_angles, tomo_angles
from libraries.settings import (SIM_MODE, COMPORT,
                                HWP_IN_2, QWP_IN_2, HWP_OUT_2, QWP_OUT_2,
                                HWP_TOM_1, QWP_TOM_1)
import time

if SIM_MODE:
    from interfaces.mock import MockSMC100Connection as _Connection, MockSMC100Stage as _Stage
else:
    import interfaces.smc100 as _smc
    _Connection = _smc.SMC100Connection
    _Stage = _smc.SMC100Stage

# Named basis sets for use by callers
HV_BASES   = ('H', 'V')
HVAD_BASES = ('H', 'V', 'A', 'D')
FULL_BASES = ('H', 'V', 'A', 'D', 'R', 'L')


def beep():
    print('\a', end='', flush=True)


def set_fixed_waveplates(angles, path=None):
    """Move any fixed-position waveplates that have non-zero angles set.

    The analyzer pair for `path` (TOM_1 for path 1, OUT_2 for path 2) is
    skipped — the tomo sweep drives it. path=None sets all pairs.
    """
    plates = [
        ('hin2', 'HWP_IN_2',  HWP_IN_2),
        ('qin2', 'QWP_IN_2',  QWP_IN_2),
        ('hf2',  'HWP_OUT_2', HWP_OUT_2),
        ('qf2',  'QWP_OUT_2', QWP_OUT_2),
        ('hf1',  'HWP_TOM_1', HWP_TOM_1),
        ('qf1',  'QWP_TOM_1', QWP_TOM_1),
    ]
    skip = {1: ('hf1', 'qf1'), 2: ('hf2', 'qf2')}.get(path, ())
    for key, name, stage in plates:
        if key in skip or angles.get(key) is None:
            continue
        print(f"Setting {name} to {angles[key]}°")
        move_stage(stage, angles[key], COMPORT)


def input_tomography(qwp, hwp, hwp_in, qwp_in, powermeter, smc_port,
                     bases: tuple = HVAD_BASES, angle_table: dict | None = None,
                     tomo_table: dict | None = None) -> dict:
    """
    Perform single_tomography for each input basis in bases.
    angle_table maps basis -> [hwp, qwp] prep angles (default: basis_angles;
    pass process_state_angles to tomo the s{j}_{N} states).
    tomo_table maps basis -> [hwp, qwp] analyzer angles for single_tomography
    (default: tomo_angles; pass basis_angles for a "forward"-wired analyzer
    pair, e.g. IN_2 used as a fibre-output analyzer).
    Returns {basis: {output_state: (power, err)}}.
    """
    table = angle_table if angle_table is not None else basis_angles
    res = {}
    for basis in bases:
        print(f"Setting New Input Basis : |{basis}>")
        move_stage(hwp_in, table[basis][0], smc_port)
        move_stage(qwp_in, table[basis][1], smc_port)
        res[basis] = single_tomography(qwp, hwp, powermeter, smc_port, angle_table=tomo_table)
    return res


def single_tomography(qwp, hwp, powermeter, smc_port, angle_table: dict | None = None) -> dict:
    """Measure all 6 output states (HVADRL) for the current input state."""
    table = angle_table if angle_table is not None else tomo_angles
    res = {}
    for basis in FULL_BASES:
        print(f"Measuring Output |{basis}>, HWP: {table[basis][0]}, QWP: {table[basis][1]}")
        move_stage(hwp, table[basis][0], smc_port)
        move_stage(qwp, table[basis][1], smc_port)
        time.sleep(0.1)
        pwr, err = powermeter.read(n=300)
        print(f"Power: {round(pwr * 1000, 2)} mW")
        res[basis] = (pwr, err)
    return res


def move_stage(this_stage, angle: float, smc_port: str) -> None:
    with _Connection(port=smc_port) as stages:
        stage = _Stage(stages, smcID=this_stage.ID)
        stage.enable()
        try:
            stage.move_absolute(angle + this_stage.OA)
        finally:
            stage.disable()
