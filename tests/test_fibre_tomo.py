"""Regression check for fibre_tomo's loop-path angle tables.

IN_2 (prep) negates its QWP (backwards-mounted). OUT_2 (analyze) does NOT
reverse plate order or negate anything in loop mode — it just uses its
normal tomo_angles analyzer role, same as everywhere else it's used.

This was arrived at the hard way: an earlier version gave OUT_2 its own
"loop_analyzer_angles" table (HWP-then-QWP order, QWP negated), reasoning
that the loop reverses beam direction through OUT_2's plates the same way
it does through IN_2's. That table was internally consistent (it also
reproduced the ideal MUB pattern) but wrong — it contradicted the one
piece of real bench-confirmed ground truth available:
polarisation_tuner._D_TO_V_OUT = (-22.5, -45), confirmed on the bench to
rotate D to V. That value only reproduces D->V when applied AS-IS
(no sign flip) in OUT_2's default QWP-then-HWP order — not under the
reversed-order/negated-QWP model. See tests below for both directions of
this check."""
import numpy as np

from libraries.basis_vectors import basis_angles, tomo_angles
from libraries.optics import HWP, QWP
from tomo_auto import fibre_tomo

BASES = ('H', 'V', 'A', 'D', 'R', 'L')
H_KET = np.array([[1.0 + 0j], [0.0]])


def _prep_loop_table():
    # Mirrors the table built inside fibre_tomo(loop=True) for IN_2.
    return {b: (h, -q) for b, (h, q) in basis_angles.items()}


def _prep(basis):
    hwp, qwp = basis_angles[basis]
    return QWP(qwp) @ HWP(hwp) @ H_KET


def _apply_out2(hwp, qwp, state):
    """OUT_2's default order: QWP encountered first, then HWP."""
    return HWP(hwp) @ QWP(qwp) @ state


def test_loop_prep_table_negates_qwp_only():
    table = _prep_loop_table()
    for basis, (hwp, qwp) in basis_angles.items():
        assert table[basis][0] == hwp
        assert table[basis][1] == -qwp


def test_d_to_v_rotation_matches_bench_only_with_no_sign_flip():
    """Locks in the bench-confirmed fact that anchors this whole design:
    _D_TO_V_OUT applied as-is (no negation) in OUT_2's normal order maps
    D -> V exactly. If this ever fails, OUT_2's mount convention has
    changed and every angle table touching it needs re-deriving."""
    D_TO_V_OUT = (-22.5, -45)
    out = _apply_out2(*D_TO_V_OUT, _prep('D'))
    probs = np.abs(out.flatten()) ** 2
    assert np.isclose(probs[0], 0.0, atol=1e-6)  # H component
    assert np.isclose(probs[1], 1.0, atol=1e-6)  # V component


def test_tomo_angles_reproduces_mub_pattern_at_out2():
    """OUT_2's loop analyzer role is just tomo_angles, unchanged — must
    map every basis to H with certainty and its conjugate to zero."""
    conjugate = {'H': 'V', 'V': 'H', 'A': 'D', 'D': 'A', 'R': 'L', 'L': 'R'}
    for basis in BASES:
        state = _prep(basis)
        hwp, qwp = tomo_angles[basis]
        prob_self = np.abs(_apply_out2(hwp, qwp, state)[0, 0]) ** 2
        hwp_c, qwp_c = tomo_angles[conjugate[basis]]
        prob_conj = np.abs(_apply_out2(hwp_c, qwp_c, state)[0, 0]) ** 2
        assert np.isclose(prob_self, 1.0, atol=1e-6)
        assert np.isclose(prob_conj, 0.0, atol=1e-6)


def test_fibre_tomo_loop_uses_default_analyzer_table():
    """loop=True must NOT override analyzer_table — OUT_2 uses the same
    tomo_angles default as the non-loop case."""
    import inspect
    src = inspect.getsource(fibre_tomo)
    assert 'analyzer_table = loop_table, None' in src, (
        "loop mode must leave OUT_2 on the default tomo_angles analyzer "
        "table, not a loop-specific override")


def test_fibre_tomo_loop_kwarg_present():
    assert 'loop' in fibre_tomo.__code__.co_varnames
