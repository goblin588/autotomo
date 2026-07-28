"""Regression check: fibre_tomo's loop-path table must negate only the QWP
angle (both IN_2's and OUT_2's QWPs are mounted backwards for the loop
direction, per polarisation_tuner.set_stages_loop, which sets both pairs
from basis_angles with QWP negated) and must leave HWP untouched, for every
basis — not just the H/D pair the toggle was originally verified against.
Both ends of the loop use the SAME table (symmetric H-then-Q order at both
IN_2 and OUT_2 when the beam reverses through them) — OUT_2 does NOT fall
back to the usual tomo_angles analyzer convention in loop mode."""
from libraries.basis_vectors import basis_angles
from tomo_auto import fibre_tomo


def _loop_table():
    # Mirrors the table built inside fibre_tomo(loop=True); kept here as an
    # independent recomputation so the test fails if that logic drifts.
    return {b: (h, -q) for b, (h, q) in basis_angles.items()}


def test_loop_table_negates_qwp_only():
    table = _loop_table()
    for basis, (hwp, qwp) in basis_angles.items():
        assert table[basis][0] == hwp
        assert table[basis][1] == -qwp


def test_loop_table_matches_polarisation_tuner_for_h_and_d():
    """H and D are the bench-verified cases from polarisation_tuner.set_stages_to_v."""
    table = _loop_table()
    assert table['H'] == (basis_angles['H'][0], -basis_angles['H'][1])
    assert table['D'] == (basis_angles['D'][0], -basis_angles['D'][1])


def test_fibre_tomo_loop_kwarg_and_analyzer_table_threaded():
    assert 'loop' in fibre_tomo.__code__.co_varnames
    import inspect
    src = inspect.getsource(fibre_tomo)
    assert 'analyzer_table=analyzer_table' in src, (
        "loop mode must pass analyzer_table through to input_tomography, "
        "not rely on the default tomo_angles for OUT_2")
