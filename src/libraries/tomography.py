"""
Functions associated with Tomography control / movement of stages.
"""

from libraries.basis_vectors import basis_angles, tomo_angles, loop_analyzer_angles
from libraries.settings import (SIM_MODE, COMPORT,
                                HWP_IN_2, QWP_IN_2, HWP_OUT_2, QWP_OUT_2,
                                HWP_TOM_1, QWP_TOM_1, HWP_1, QWP_1, HWP_12, QWP_12)
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

# Power-meter samples averaged per output-basis read. Bigger n = tighter
# error bars but slower (SEM ~ 1/sqrt(n)); 300->50 was a 6x speedup for a
# ~2.45x wider SEM (2026-11-09).
N_READS = 50


def beep():
    print('\a', end='', flush=True)


def open_connection(smc_port: str = COMPORT):
    """Open one serial connection, to be reused across multiple move_stage
    calls (pass it as `connection=`) instead of opening a fresh connection
    per move."""
    return _Connection(port=smc_port)


def set_fixed_waveplates(angles, path=None, connection=None):
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
        ('h1',   'HWP_1',     HWP_1),
        ('q1',   'QWP_1',     QWP_1),
        ('h2',   'HWP_12',    HWP_12),
        ('q2',   'QWP_12',    QWP_12),
    ]
    skip = {1: ('hf1', 'qf1'), 2: ('hf2', 'qf2')}.get(path, ())
    for key, name, stage in plates:
        if key in skip or angles.get(key) is None:
            continue
        print(f"Setting {name} to {angles[key]}°")
        move_stage(stage, angles[key], COMPORT, connection=connection)


def input_tomography(qwp, hwp, hwp_in, qwp_in, powermeter, smc_port,
                     bases: tuple = HVAD_BASES, angle_table: dict | None = None,
                     analyzer_table: dict | None = None, on_progress=None,
                     connection=None) -> dict:
    """
    Perform single_tomography for each input basis in bases.
    angle_table maps basis -> [hwp, qwp] prep angles (default: basis_angles;
    pass process_state_angles to tomo the s{j}_{N} states).
    analyzer_table maps basis -> [hwp, qwp] analyzer angles (default:
    tomo_angles; pass a different table when the analyzer pair's beam
    order/mount isn't the usual QWP-then-HWP, e.g. the loop's OUT_2).
    on_progress: called after every single output-basis measurement (so
    once per input basis x output basis pair), for progress reporting.
    connection: an already-open connection (from open_connection()) to reuse
    for every move instead of opening one per move.
    Returns {basis: {output_state: (power, err)}}.
    """
    table = angle_table if angle_table is not None else basis_angles
    res = {}
    for basis in bases:
        print(f"Setting New Input Basis : |{basis}>")
        move_stage(hwp_in, table[basis][0], smc_port, connection=connection)
        move_stage(qwp_in, table[basis][1], smc_port, connection=connection)
        res[basis] = single_tomography(qwp, hwp, powermeter, smc_port,
                                        analyzer_table=analyzer_table, on_progress=on_progress,
                                        connection=connection)
    return res


def single_tomography(qwp, hwp, powermeter, smc_port, analyzer_table: dict | None = None,
                      on_progress=None, connection=None) -> dict:
    """Measure all 6 output states (HVADRL) for the current input state."""
    table = analyzer_table if analyzer_table is not None else tomo_angles
    res = {}
    for basis in FULL_BASES:
        print(f"Measuring Output |{basis}>, HWP: {table[basis][0]}, QWP: {table[basis][1]}")
        move_stage(hwp, table[basis][0], smc_port, connection=connection)
        move_stage(qwp, table[basis][1], smc_port, connection=connection)
        time.sleep(0.1)
        pwr, err = powermeter.read(n=N_READS)
        print(f"Power: {round(pwr * 1000, 2)} mW")
        res[basis] = (pwr, err)
        if on_progress is not None:
            on_progress()
    return res


def _move(stages, this_stage, angle: float) -> None:
    stage = _Stage(stages, smcID=this_stage.ID)
    stage.enable()
    try:
        stage.move_absolute(angle + this_stage.OA)
    finally:
        stage.disable()


def move_stage(this_stage, angle: float, smc_port: str, connection=None) -> None:
    """Move a single stage. Pass an already-open connection (from
    open_connection()) to reuse it across many moves instead of opening a
    fresh serial connection per call."""
    if connection is not None:
        _move(connection, this_stage, angle)
    else:
        with _Connection(port=smc_port) as stages:
            _move(stages, this_stage, angle)
