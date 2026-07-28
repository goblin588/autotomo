"""Regression check for fibre_tomo's loop-path angle tables.

IN_2 (prep) and OUT_2 (analyze) are NOT the same table, despite both being
HWP-then-QWP order in loop mode: preparing H->basis and projecting
basis->H through the same plate order need different QWP angles (only
coincide when the basis's own QWP angle is 0, i.e. H/V). This was the bug —
OUT_2 used to reuse the negated basis_angles prep table, which is why real
tomography on A/D/R/L loop inputs came out wrong (verified against
optics.py Jones matrices below)."""
import numpy as np

from libraries.basis_vectors import basis_angles, loop_analyzer_angles
from libraries.optics import HWP, QWP
from tomo_auto import fibre_tomo

BASES = ('H', 'V', 'A', 'D', 'R', 'L')
H_KET = np.array([[1.0 + 0j], [0.0]])


def _prep_loop_table():
    # Mirrors the table built inside fibre_tomo(loop=True) for IN_2.
    return {b: (h, -q) for b, (h, q) in basis_angles.items()}


def test_loop_prep_table_negates_qwp_only():
    table = _prep_loop_table()
    for basis, (hwp, qwp) in basis_angles.items():
        assert table[basis][0] == hwp
        assert table[basis][1] == -qwp


def test_loop_analyzer_table_reproduces_mub_pattern():
    """OUT_2's loop_analyzer_angles are commanded angles: OUT_2's QWP is
    mounted backwards (same convention as IN_2's), so the physical QWP
    rotation is -1 * the commanded value. Simulating that physical
    rotation, applied HWP-then-QWP, must map every basis to H with
    certainty and to its conjugate basis with zero probability
    (identity/1/0.5 MUB pattern) — or the bench will see scrambled or
    lost power exactly like the reported A/D/R/L symptoms."""
    def prep(basis):
        hwp, qwp = basis_angles[basis]
        return QWP(qwp) @ HWP(hwp) @ H_KET

    def prob_h(basis, state):
        command_hwp, command_qwp = loop_analyzer_angles[basis]
        physical_hwp, physical_qwp = command_hwp, -command_qwp
        out = QWP(physical_qwp) @ HWP(physical_hwp) @ state
        return abs(out[0, 0]) ** 2

    conjugate = {'H': 'V', 'V': 'H', 'A': 'D', 'D': 'A', 'R': 'L', 'L': 'R'}
    for basis in BASES:
        state = prep(basis)
        assert np.isclose(prob_h(basis, state), 1.0, atol=1e-6)
        assert np.isclose(prob_h(conjugate[basis], state), 0.0, atol=1e-6)


def test_loop_analyzer_table_differs_from_naive_negation_except_h_v():
    """H/V happen to coincide with the old (wrong) negated-basis_angles
    formula because their prep QWP is 0; A/D/R/L must not."""
    naive = _prep_loop_table()
    for basis in ('A', 'D', 'R', 'L'):
        assert tuple(loop_analyzer_angles[basis]) != naive[basis]
    for basis in ('H', 'V'):
        assert tuple(loop_analyzer_angles[basis]) == naive[basis]


def test_fibre_tomo_loop_kwarg_and_analyzer_table_threaded():
    assert 'loop' in fibre_tomo.__code__.co_varnames
    import inspect
    src = inspect.getsource(fibre_tomo)
    assert 'analyzer_table=analyzer_table' in src, (
        "loop mode must pass analyzer_table through to input_tomography, "
        "not rely on the default tomo_angles for OUT_2")
